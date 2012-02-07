''' This module includes the view functions which implement the various
search pages.
'''

# standard python packages
import types

# django packages
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.db import connection
from django.db.models import Q, Max
from django.http import HttpResponse, Http404, HttpResponseRedirect
from django.core.paginator import Paginator, InvalidPage, EmptyPage
from django.utils.decorators import method_decorator
from django.views.generic import View, DetailView
from django.views.generic.edit import TemplateResponseMixin, CreateView, UpdateView

# Provides conversion to Excel format
from xlwt import Workbook

# project specific packages
from forms import *
from models import MethodVW, MethodSummaryVW, MethodAnalyteVW, DefinitionsDOM, AnalyteCodeRel, MethodAnalyteAllVW, MethodAnalyteJnStgVW, MethodStgSummaryVw
from models import SourceCitationRef

def _get_choice_select(field):
    '''Returns the visible choice from the form field variable. The function
    assumes choice values are integer or string
    '''
    if type(field.field.choices[1][0]) is types.IntType:
        return dict(field.field.choices).get(int(field.data))
    return dict(field.field.choices).get(field.data)

def _get_criteria(field):
    ''' Assumes that the field is a ChoiceField.
    Returns a tuple if the field value is not 'all', where the first element is the label
    of field and the second element is the visible choice for field.
    '''
    if field.data == 'all':
        return None
    else:
        return (field.label, _get_choice_select(field))
    
def _get_criteria_with_name(form, field_name):
    '''Returns a tuple representing field_name's label and choice from form.
    '''
    if form.cleaned_data[field_name] == None:
        return None
    
    else:
        return (form[field_name].label, form.cleaned_data[field_name])
    
def _get_multi_choice_criteria(form, name):
    choice_dict = dict(form[name].field.choices)
    if len(form.cleaned_data[name]) == len(choice_dict):
        return []
    else:
        if type(choice_dict.keys()[0]) is types.IntType:
            return [choice_dict.get(int(k)) for k in form.cleaned_data[name]]
        else:
            return [choice_dict.get(k) for k in form.cleaned_data[name]]
    

def _dictfetchall(cursor):
    '''Returns all rows from the cursor query as a dictionary with the key value equal to column name in uppercase'''
    desc = cursor.description
    return [
            dict(zip([col[0] for col in desc], row))
            for row in cursor.fetchall()
            ]
               
def _greenness_profile(d):
    '''Returns a dicitionary with five keywords. The first keyword is profile whose is 
    a list of four gifs representing the greenness profile of the dictionary d or an empty list if there is not
    enough information for a complete profile. The second through 5th keyword represent the verbose greenness value for
    pbt, toxic, corrisive, and waste_amt
    '''
    def _g_value(flag):
        ''' Returns a string representing the verbose "greenness" of flag.'''
        if flag == 'N':
            return 'Green'
        elif flag == 'Y':
            return 'Not Green'
        else:
            return 'N.S.'
        
    pbt = d.get('pbt', '')
    toxic = d.get('toxic', '')
    corrosive = d.get('corrosive', '')
    waste = d.get('waste', '')
    
    g = []
    if pbt == 'N':
        g.append('ULG2.gif')
    elif pbt == 'Y':
        g.append('ULW2.gif')
        
    if toxic == 'N':
        g.append('URG2.gif')
    elif toxic == 'Y':
        g.append('URW2.gif')
        
    if corrosive == 'N':
        g.append('LLG2.gif')
    elif corrosive == 'Y':
        g.append('LLW2.gif')
        
    if waste == 'N':
        g.append('LRG2.gif')
    elif waste == 'Y':
        g.append('LRW2.gif')
        
    if len(g) != 4:
        g = []

    return {'profile' : g, 
            'pbt' : _g_value(pbt), 
            'hazardous' : _g_value(toxic),
            'corrosive' : _g_value(corrosive),
            'waste_amt' : _g_value(waste)}
    
def _tsv_response(headings, vl_qs):
    ''' Returns an http response which contains a tab-separate-values file
    representing the values list query set, vl_qs, and using headings as the 
    column headers.
    '''
    response = HttpResponse(mimetype='text/tab-separated-values')
    response['Content-Disposition'] = 'attachment; filename=general_search.tsv'

    response.write('\t'.join(headings))
    response.write('\n')

    for row in vl_qs:
        for col in row:
            response.write('%s\t' % str(col))
        response.write('\n')

    return response

def _xls_response(headings, vl_qs):
    '''Returns an http response which contains an Excel file
    representing the values list query set, vl_qs, and using headings
    as the column headers.
    '''
    response = HttpResponse(mimetype='application/vnd.ms-excel')
    response['Content-Disposition'] = 'attachment; filename=general_search.xls'
    
    wb = Workbook()
    ws = wb.add_sheet('sheet 1')
    
    for col_i in range(len(headings)):
        ws.write(0, col_i, headings[col_i])
    
    for row_i in range(len(vl_qs)):
        for col_i in range(len(vl_qs[row_i])):
            ws.write(row_i + 1, col_i, vl_qs[row_i][col_i])
    
    wb.save(response)
    
    return response

def _analyte_value_qs(method_id):
    ''' Returns the analyte data values query set for the method_id.'''
    
    analyte_data = MethodAnalyteVW.objects.filter(preferred__exact=-1, method_id__exact=method_id).order_by('analyte_name')
    return analyte_data.values('analyte_name',
                               'analyte_code',
                               'dl_value',
                               'dl_units_description',
                               'dl_units',
                               'accuracy',
                               'accuracy_units_description',
                               'accuracy_units',
                               'precision',
                               'precision_units_description',
                               'precision_units',
                               'false_positive_value',
                               'false_negative_value',
                               'prec_acc_conc_used').distinct()
 
class FilterFormMixin(View):
    
    form_class = Form

    def get_qs(self, form):
        return None
    
    def get_context_data(self, form):
        return {'form' : form}
    
                                
        
class SearchResultView(View, TemplateResponseMixin):
    ''' This class extends the standard view and template response mixin. The class should be extended along with
    the SearchFormMixin to implement the search pages.
    '''
    
    result_fields = () # Fields to be displayed on the results page
    result_field_order_by = '' #Field to order the query results. If null, no order is specified
    
    header_abbrev_set = () # The header definitions to retrieve from the DOM. These should be in the order (from left to right)
    # that they will appear on the screen
    
    def get_header_defs(self):
        ''' Returns a list of DefinitionsDOM objects matching the definition_abbrev using abbrev_set. 
        The objects will only have the definition_name and definition_description field set.
        The objects will be in the same order as abbrev_set and if an object is missing or there are multiple
        in the DefinitionsDOM table, then the name in abbrev_set is used with spaces replacing underscores and words
        capitalized with a standard description.
        '''
        def_qs = DefinitionsDOM.objects.filter(definition_abbrev__in=self.header_abbrev_set)
        
        header_defs = []
        for abbrev in self.header_abbrev_set:
            try:
                header_defs.append(def_qs.get(definition_abbrev=abbrev))
            except(DefinitionsDOM.MultipleObjectsReturned, DefinitionsDOM.DoesNotExist):
                header_defs.append(DefinitionsDOM(definition_name=abbrev.replace('_', ' ').title(),
                                                  definition_description='No definition available.')) 
            
        return header_defs

    def get_values_qs(self, qs):
        ''' Returns the qs as a values query set with result_fields in the set and ordered by result_field_order_by.'''
        v_qs = qs.values(*self.result_fields).distinct()
        if self.result_field_order_by:
            v_qs = v_qs.order_by(self.result_field_order_by)
            
        return v_qs
    
    def get_results_context(self, qs):
        '''Returns the results context variable. By default this returns self.get_values_qs().
        If you need to process the values query set further, override this method.
        '''
        return self.get_values_qs(qs)

    def get(self, request, *args, **kwargs):
        '''Process the GET request.'''
        if request.GET:
            form = self.form_class(request.GET)
            if form.is_valid():
                context = {'search_form' : form,
                           'results' : self.get_results_context(self.get_qs(form)),
                           'query_string' : '?' + request.get_full_path().split('&', 1)[1],
                           'header_defs' : self.get_header_defs(),
                           'hide_search' : True,
                           'show_results' : True}
                context.update(self.get_context_data(form))
                
                return self.render_to_response(context)          
             
            else:
                return self.render_to_response({'search_form' : form,
                                        'hide_search' : False,
                                        'show_results' : False}) 
            
        else:
            return self.render_to_response({'search_form' : self.form_class(),
                                            'hide_search' : False,
                                            'show_results' : False})
                
class ExportSearchView(View):
    ''' This class extends the standard View to implement the view which exports the search results
    table. This should be extended along with the SearchFormMixin.
    '''

    export_fields = () # Fields in the query set to be exported to file
    export_field_order_by = '' # Field name to order the export query results by. If null, no order is specified
    
    def get_export_qs(self, qs):
        ''' Return a values list query set from the objects query set using export_fields to select fields
        and export_field_order_by to order the query set.
        '''
        export_qs = qs.values_list(*self.export_fields).distinct()
        if self.export_field_order_by:
            export_qs = export_qs.order_by(self.export_field_order_by)
            
        return export_qs
    

    def get(self, request, *args, **kwargs):
        '''Processes the get request.'''
        if request.GET:
            form = self.form_class(request.GET)
            if form.is_valid():
                HEADINGS = [name.replace('_', ' ').title() for name in self.export_fields]
                export_type = kwargs.get('export', '')
                
                if export_type == 'tsv':
                    return _tsv_response(HEADINGS, self.get_export_qs(self.get_qs(form)))
                
                elif export_type == 'xls':
                    return _xls_response(HEADINGS, self.get_export_qs(self.get_qs(form)))
                
                else:
                    return Http404
            
            else:
                return Http404
            
        else:
            return Http404
                
class GeneralSearchFormMixin(FilterFormMixin):
    '''Extends the SearchFormMixin to implement the search form used on the General Search page.'''

    form_class = GeneralSearchForm
    
    def get_qs(self, form):
        qs = MethodVW.objects.all()

        if form.cleaned_data['media_name'] != 'all':
            qs = qs.filter(media_name__exact=form.cleaned_data['media_name'])

        if form.cleaned_data['source'] != 'all':
            qs = qs.filter(method_source__contains=form.cleaned_data['source'])

        if form.cleaned_data['method_number'] != 'all':
            qs = qs.filter(method_id__exact=int(form.cleaned_data['method_number']))
            
        if form.cleaned_data['instrumentation'] != 'all':
            qs = qs.filter(instrumentation_id__exact=int(form.cleaned_data['instrumentation']))  
        
        if form.cleaned_data['method_subcategory'] != 'all':
            qs = qs.filter(method_subcategory_id__exact=int(form.cleaned_data['method_subcategory']))
        
        qs = qs.filter(method_type_id__in=form.cleaned_data['method_types'])
        
        return qs
        
    def get_context_data(self, form):
        criteria = []
        criteria.append(_get_criteria(form['media_name']))
        criteria.append(_get_criteria(form['source']))
        criteria.append(_get_criteria(form['method_number']))
        criteria.append(_get_criteria(form['instrumentation']))
        criteria.append(_get_criteria(form['method_subcategory']))
        
        return {'criteria' : criteria,
                'selected_method_types' : _get_multi_choice_criteria(form, 'method_types')}
    

#        method_type_dict = dict(self.search_form['method_types'].field.choices)
#        if len(self.search_form.cleaned_data['method_types']) == len(method_type_dict):
#            selected_method_types = []
#        else:
#            selected_method_types = [method_type_dict.get(int(k)) for k in self.search_form.cleaned_data['method_types']]
        
#        self.qs = self.qs.filter(method_type_id__in=self.search_form.cleaned_data['method_types']) 
        
        
class ExportGeneralSearchView(ExportSearchView, GeneralSearchFormMixin):
    '''Extends the ExportSearchView and GeneralSearchFormMixin to implement the
    general search export file generation.
    '''
    export_fields = ('method_id', 
                     'source_method_identifier',
                     'method_descriptive_name', 
                     'media_name', 
                     'method_source',
                     'instrumentation_description',
                     'method_subcategory',
                     'method_category',
                     'method_type_desc')
    export_field_order_by = 'source_method_identifier'
               
class GeneralSearchView(GeneralSearchFormMixin, SearchResultView):
    '''Extends the SearchResultView and GeneralSearchFormMixin to implement the
    general search page.
    '''
    result_fields = ('source_method_identifier',
                     'method_source',
                     'instrumentation_description',
                     'method_descriptive_name',
                     'media_name',
                     'method_category',
                     'method_subcategory',
                     'method_type_desc',
                     'method_id',
                     'assumptions_comments',
                     'pbt',
                     'toxic',
                     'corrosive',
                     'waste')
    
    header_abbrev_set = ('SOURCE_METHOD_IDENTIFIER',
                         'METHOD_DESCRIPTIVE_NAME',
                         'MEDIA_NAME',
                         'METHOD_SOURCE',
                         'INSTRUMENTATION',
                         'METHOD_CATEGORY',
                         'METHOD_SUBCATEGORY',
                         'METHOD_TYPE',
                         'GREENNESS')
    
    template_name = 'general_search.html'
    
    def get_results_context(self, qs):
        '''Returns a list of dictionaries where each element in the list contains two keywords.
        The keyword m contains a model object in self.get_values_qs. The keyword, greenness,
        contains the greenness profile information for that object.
        '''
        return [{'m' : r, 'greenness': _greenness_profile(r)} for r in self.get_values_qs(qs)] 
                    
class AnalyteSearchFormMixin(FilterFormMixin):
    '''Extends the SearchFormMixin to implement the Analyte search form used on the analyte search pages.'''
    
    form_class = AnalyteSearchForm
    
    def get_qs(self, form):
        qs = MethodAnalyteAllVW.objects.all()
    
        if form.cleaned_data['analyte_kind'] == 'code':
            qs = qs.filter(analyte_code__iexact=form.cleaned_data['analyte_value'])
        else: # assume analyte kind is name
            qs = qs.filter(analyte_name__iexact=form.cleaned_data['analyte_value'])
            
        if form.cleaned_data['media_name'] != 'all':
            qs = qs.filter(media_name__exact=form.cleaned_data['media_name'])
        
        if form.cleaned_data['source'] != 'all':
            qs = qs.filter(method_source__contains=form.cleaned_data['source'])
            
        if form.cleaned_data['instrumentation'] != 'all':
            qs = qs.filter(instrumentation_id__exact=form.cleaned_data['instrumentation'])
            
        if form.cleaned_data['method_subcategory'] != 'all':
            qs = qs.filter(method_subcategory_id__exact=form.cleaned_data['method_subcategory'])

        qs = qs.filter(method_type_desc__in=form.cleaned_data['method_types'])
        return qs
        
    def get_context_data(self, form):
        criteria = []
        if form.cleaned_data['analyte_kind'] == 'code':
            criteria.append(('Analyte code', form.cleaned_data['analyte_value']))
        else:
            criteria.append(('Analyte name', form.cleaned_data['analyte_value']))
        criteria.append(_get_criteria(form['media_name']))
        criteria.append(_get_criteria(form['source']))
        criteria.append(_get_criteria(form['instrumentation']))
        criteria.append(_get_criteria(form['method_subcategory']))

        return {'criteria' : criteria,
                'selected_method_types' : _get_multi_choice_criteria(form, 'method_types')}

class ExportAnalyteSearchView(ExportSearchView, AnalyteSearchFormMixin):
    '''Extends the ExportSearchView and AnalyteSearchFormMixin to implement the export analyte search feature.'''
    
    export_fields = ('method_id',
                     'method_descriptive_name',
                     'method_subcategory',
                     'method_category',
                     'method_source_id',
                     'method_source',
                     'source_method_identifier',
                     'analyte_name',
                     'analyte_code',
                     'media_name',
                     'instrumentation',
                     'instrumentation_description',
                     'sub_dl_value',
                     'dl_units',
                     'dl_type',
                     'dl_type_description',
                     'dl_units_description',
                     'sub_accuracy',
                     'accuracy_units',
                     'accuracy_units_description',
                     'sub_precision',
                     'precision_units',
                     'precision_units_description',
                     'false_negative_value',
                     'false_positive_value',
                     'prec_acc_conc_used',
                     'precision_descriptor_notes',
                     'relative_cost',
                     'relative_cost_symbol')
    export_field_order_by = 'method_id'
    
class AnalyteSearchView(SearchResultView, AnalyteSearchFormMixin):
    '''Extends the SearchResultsView and AnalyteSearchFormMixin to implement the analyte search page.'''
    
    template_name = 'analyte_search.html'
    
    result_fields = ('method_source_id',
                     'method_id',
                     'source_method_identifier',
                     'method_source',
                     'method_descriptive_name',
                     'dl_value',
                     'dl_units_description',
                     'dl_type_description',
                     'dl_type',
                     'accuracy',
                     'accuracy_units_description',
                     'accuracy_units',
                     'precision',
                     'precision_units_description',
                     'precision_units',
                     'prec_acc_conc_used',
                     'dl_units',
                     'instrumentation_description',
                     'instrumentation',
                     'relative_cost',
                     'relative_cost_symbol',
                     'pbt',
                     'toxic',
                     'corrosive',
                     'waste',
                     'assumptions_comments')
    
    header_abbrev_set = ('SOURCE_METHOD_IDENTIFIER',
                      'METHOD_SOURCE',
                      'METHOD_DESCRIPTIVE_NAME',
                      'DL_VALUE',
                      'DL_TYPE',
                      'ACCURACY',
                      'PRECISION',
                      'PREC_ACC_CONC_USED',
                      'INSTRUMENTATION',
                      'RELATIVE_COST',
                      'GREENNESS')
    
    def get_results_context(self, qs):
        '''Returns a list of dictionaries where each element in the list contains two keywords.
        The keyword m contains a model object in self.get_values_qs. The keyword, greenness,
        contains the greenness profile information for that object.
        '''
        return [{'m' : r, 'greenness' : _greenness_profile(r)} for r in self.get_values_qs(qs)] 

class AnalyteSelectView(View, TemplateResponseMixin):
    ''' Extends the standard view to implement the analyte select pop up page. '''

    template_name = 'find_analyte.html'
    
    def get(self, request, *args, **kwargs):
        if request.GET:
            select_form = AnalyteSelectForm(request.GET)
            kind = request.GET.get('kind', 'name')
            
        else:
            select_form = AnalyteSelectForm(request.GET)
            kind = 'name'
            
        return self.render_to_response({'select_form' : select_form,
                                        'kind' : kind})
        

class MicrobiologicalSearchView(SearchResultView, FilterFormMixin):
    '''Extends the SearchResultView and SearchFormMixin to implement the microbiological search page.'''
    
    template_name = "microbiological_search.html"
    form_class = MicrobiologicalSearchForm
    
    result_fields = ('method_id',
                     'source_method_identifier',
                     'method_descriptive_name',
                     'method_source',
                     'method_source_contact',
                     'method_source_url',
                     'media_name',
                     'instrumentation_description',
                     'relative_cost_symbol',
                     'cost_effort_key')
    header_abbrev_set = ('SOURCE_METHOD_IDENTIFIER',
                         'METHOD_DESCRIPTIVE_NAME',
                         'METHOD_SOURCE',
                         'MEDIA_NAME',
                         'GEAR_TYPE',
                         'RELATIVE_COST')
    
    def get_qs(self, form):
        qs = MethodAnalyteAllVW.objects.filter(method_subcategory_id__exact=5)
        
        if form.cleaned_data['analyte'] != 'all':
            qs = qs.filter(analyte_id__exact=form.cleaned_data['analyte'])
            
        qs = qs.filter(method_type_desc__in=form.cleaned_data['method_types'])
        return qs
    
    def get_context_data(self, form):
        criteria = []
        criteria.append(_get_criteria(form['analyte']))
    
        return {'criteria' : criteria,
                'selected_method_types' : _get_multi_choice_criteria(form, 'method_types')}
        
class BiologicalSearchView(SearchResultView, FilterFormMixin):
    '''Extends the SearchResultView and SearchFormMixin to implement the biological search page.'''
    
    template_name = 'biological_search.html'
    form_class = BiologicalSearchForm
    
    result_fields = ('method_id',
                     'source_method_identifier',
                     'method_descriptive_name',
                     'analyte_type',
                     'method_source',
                     'method_source_contact',
                     'method_source_url',
                     'method_type_desc',
                     'media_name',
                     'waterbody_type',
                     'instrumentation_description',
                     'relative_cost_symbol',
                     'cost_effort_key')
    
    header_abbrev_set = ('ANALYTE_TYPE',
                         'SOURCE_METHOD_IDENTIFIER',
                         'METHOD_DESCRIPTIVE_NAME',
                         'METHOD_SOURCE',
                         'METHOD_TYPE',
                         'MEDIA_NAME',
                         'WATERBODY_TYPE',
                         'GEAR_TYPE',
                         'RELATIVE_COST')
    def get_qs(self, form):
        qs = MethodAnalyteAllVW.objects.filter(method_subcategory_id=7)
        
        if form.cleaned_data['analyte_type'] != 'all':
            qs = qs.filter(analyte_type__exact=form.cleaned_data['analyte_type'])
            
        if form.cleaned_data['waterbody_type'] != 'all':
            qs = qs.filter(waterbody_type__exact=form.cleaned_data['waterbody_type'])
            
        if form.cleaned_data['gear_type'] != 'all':
            qs = qs.filter(instrumentation_id__exact=form.cleaned_data['gear_type'])
        
        qs = qs.filter(method_type_desc__in=form.cleaned_data['method_types']) 
        
        return qs
    
    def get_context_data(self, form):
        criteria = []
        criteria.append(_get_criteria(form['analyte_type']))
        criteria.append(_get_criteria(form['waterbody_type']))
        criteria.append(_get_criteria(form['gear_type']))
        
        return {'criteria' : criteria,
                'selected_method_types' : _get_multi_choice_criteria(form, 'method_types')}
           

        
class ToxicitySearchView(SearchResultView, FilterFormMixin):
    '''Extends the SearchResultsView and SearchFormMixin to implements the toxicity search page.'''
    
    template_name = 'toxicity_search.html'
    form_class = ToxicitySearchForm
    
    result_fields = ('method_id', 
                    'source_method_identifier',
                    'method_descriptive_name',
                    'method_subcategory',
                    'method_source',
                    'method_source_contact',
                    'method_source_url',
                    'media_name',
                    'matrix',
                    'relative_cost_symbol',
                    'cost_effort_key')
    
    header_abbrev_set = ('SOURCE_METHOD_IDENTIFIER',
                         'METHOD_DESCRIPTIVE_NAME',
                         'METHOD_SUBCATEGORY',
                         'METHOD_SOURCE',
                         'MEDIA_NAME',
                         'MATRIX',
                         'RELATIVE_COST')
    
    def get_qs(self, form):
        qs = MethodAnalyteAllVW.objects.filter(method_category__exact='TOXICITY ASSAY').exclude(source_method_identifier__exact='ORNL-UDLP-01')
        
        if form.cleaned_data['subcategory'] != 'all':
            qs = qs.filter(method_subcategory__exact=form.cleaned_data['subcategory'])
            
        if form.cleaned_data['media'] != 'all':
            qs = qs.filter(media_name__exact=form.cleaned_data['media'])
            
        if form.cleaned_data['matrix'] != 'all':
            qs = qs.filter(matrix__exact=form.cleaned_data['matrix'])
            
        qs = qs.filter(method_type_desc__in=form.cleaned_data['method_types'])
        
        return qs
        
    def get_context_data(self, form):
        criteria = []
        criteria.append(_get_criteria(form['subcategory']))
        criteria.append(_get_criteria(form['media']))
        criteria.append(_get_criteria(form['matrix']))
        
        return {'criteria' : criteria,
                'selected_method_types' : _get_multi_choice_criteria(form, 'method_types')}
        
class PhysicalSearchView(SearchResultView, FilterFormMixin):
    
    template_name = 'physical_search.html'
    form_class = PhysicalSearchForm
    
    result_fields = ('method_id',
                     'source_method_identifier',
                     'method_descriptive_name',
                     'method_source',
                     'method_source_contact',
                     'method_source_url',
                     'media_name',
                     'instrumentation_description')
    
    header_abbrev_set = ('SOURCE_METHOD_IDENTIFIER',
                         'METHOD_DESCRIPTIVE_NAME',
                         'METHOD_SOURCE',
                         'MEDIA_NAME',
                         'GEAR_TYPE')
    def get_qs(self, form):
        qs = MethodAnalyteAllVW.objects.filter(method_subcategory_id__exact=9)        
        if form.cleaned_data['analyte'] != 'all':
            qs = qs.filter(analyte_id__exact=form.cleaned_data['analyte'])

        qs = qs.filter(method_type_desc__in=form.cleaned_data['method_types']) 
        
        return qs
    
    def get_context_data(self, form):
        criteria = []
        criteria.append(_get_criteria(form['analyte']))
        
        return {'criteria' : criteria,
                'selected_method_types' : _get_multi_choice_criteria(form, 'method_types')}
            
    
class StreamPhysicalSearchView(SearchResultView, TemplateResponseMixin):
    
    template_name="stream_physical_search.html"
    
    result_fields = ('method_id',
                     'source_method_identifier',
                     'method_descriptive_name',
                     'method_source',
                     'method_source_contact',
                     'method_source_url',
                     'media_name',
                     'relative_cost_symbol',
                     'cost_effort_key')
    
    header_abbrev_set = ('SOURCE_METHOD_IDENTIFIER',
                       'METHOD_DESCRIPTIVE_NAME',
                       'METHOD_SOURCE',
                       'MEDIA_NAME',
                       'RELATIVE_COST'
                       )
    
    qs = MethodAnalyteJnStgVW.objects.filter(source_method_identifier__startswith='WRIR')

    def get(self, request, *args, **kwargs):
        return self.render_to_response({'header_defs' : self.get_header_defs(),
                                'results' : self.get_results_context(self.qs),
                                'show_results' : True})                

class KeywordSearchView(View, TemplateResponseMixin):
    '''Extends the standard View to implement the keyword search view. This form only
    processes get requests.
    '''  
    
    template_name = "keyword_search.html"
    
    def get(self, request, *args, **kwargs):
        '''Returns the http response for the keyword search form. If the form is bound
        validate the form and the execute a raw SQL query to return matching methods. The resulting 
        query set will be shown using pagination and in score order.
        '''
        if request.GET:
            # Form has been submitted.
            form = KeywordSearchForm(request.GET)
            if form.is_valid():
                # Execute as raw query since  it uses a CONTAINS clause and context grammer.
                cursor = connection.cursor() #@UndefinedVariable
                cursor.execute('SELECT DISTINCT score(1) method_summary_score, mf.method_id, mf.source_method_identifier method_number, \
mf.link_to_full_method, mf.mimetype, mf.revision_id, mf.method_official_name, mf.method_descriptive_name, mf.method_source \
FROM nemi_data.method_fact mf, nemi_data.revision_join rj \
WHERE mf.revision_id = rj.revision_id AND \
(CONTAINS(mf.source_method_identifier, \'<query><textquery lang="ENGLISH" grammar="CONTEXT">' + form.cleaned_data['keywords'] + '.<progression> \
<seq><rewrite>transform((TOKENS, "{", "}", " "))</rewrite></seq>\
<seq><rewrite>transform((TOKENS, "{", "}", " ; "))</rewrite></seq>\
<seq><rewrite>transform((TOKENS, "{", "}", "AND"))</rewrite></seq>\
<seq><rewrite>transform((TOKENS, "{", "}", "ACCUM"))</rewrite></seq>\
</progression></textquery><score datatype="INTEGER" algorithm="COUNT"/></query>\', 1) > 1 \
OR CONTAINS(rj.method_pdf, \'<query><textquery lang="ENGLISH" grammar="CONTEXT">' + form.cleaned_data['keywords'] + '.<progression> \
<seq><rewrite>transform((TOKENS, "{", "}", " "))</rewrite></seq>\
<seq><rewrite>transform((TOKENS, "{", "}", " ; "))</rewrite></seq>\
<seq><rewrite>transform((TOKENS, "{", "}", "AND"))</rewrite></seq>\
<seq><rewrite>transform((TOKENS, "{", "}", "ACCUM"))</rewrite></seq>\
</progression></textquery><score datatype="INTEGER" algorithm="COUNT"/></query>\', 2) > 1) \
ORDER BY score(1) desc;')
                results_list = _dictfetchall(cursor)
                paginator = Paginator(results_list, 20)
                
                try:
                    page = int(request.GET.get('page', '1'))
                except ValueError:
                    page = 1

                # If page request is out of range, deliver last page of results.
                try:
                    results = paginator.page(page)
                except (EmptyPage, InvalidPage):
                    results = paginator.page(paginator.num_pages)

                path = request.get_full_path()
                # Remove the &page parameter.
                current_url = path.rsplit('&page=')[0]
                return self.render_to_response({'form': form,
                                                'current_url' : current_url,
                                                'results' : results}) 
                
            else:
                # There is an error in form validation so resubmit the form.
                return self.render_to_response({'form' : form})

        else:
            #Render a blank form
            form = KeywordSearchForm()
            return self.render_to_response({'form' : form})
        
class BaseMethodSummaryView(View, TemplateResponseMixin):
    '''Extends the basic view to implement a method summary page. This class
    should be extended to implement specific pages by at least providing
    a template_name parameter.
    '''
    
    def get_context(self, request, *args, **kwargs):
        '''Returns additional context information to be sent to the template'''
        return {}
        
    def get(self, request, *args, **kwargs):
        '''Processes the get request and returns the appropriate http response.
        The method summary information for a method id is retrieved from MethodSummaryVW
        using the method_id passed as a keyword argument. The method's analytes are
        retrieved along with each analyte's synonymns.
        '''
        if 'method_id' in kwargs:
            try: 
                data = MethodSummaryVW.objects.get(method_id=kwargs['method_id'])
            except MethodSummaryVW.DoesNotExist:
                data = None
                
            #Get analytes for the method and each analyte's synonyms.
            analyte_data = []
            
            analyte_qs = _analyte_value_qs(kwargs['method_id'])
            for r in analyte_qs:
                name = r['analyte_name'].lower()
                code = r['analyte_code'].lower()
                inner_qs = AnalyteCodeRel.objects.filter(Q(analyte_name__iexact=name)|Q(analyte_code__iexact=code)).values_list('analyte_code', flat=True).distinct()
                qs = AnalyteCodeRel.objects.all().filter(analyte_code__in=inner_qs).order_by('analyte_name').values('analyte_name')
                syn = []
                for a in qs:
                    syn.append(a['analyte_name'])
                    
                analyte_data.append({'r' : r, 'syn' : syn})
                
            context = self.get_context(request, *args, **kwargs)
            context['data'] = data
            context['analyte_data'] = analyte_data
            return self.render_to_response(context)
    
        else:
            raise Http404

class MethodSummaryView(BaseMethodSummaryView):   
    ''' Extends the BaseMethodSummaryView to implement the standard Method Summary page.'''

    template_name='method_summary.html'
    
    def get_context(self, request, *args, **kwargs):
        '''Returns a dictionary with one keyword, 'notes' which contains a value query set generated from MethodAnalyteVw which
        contains the two fields, precision_descriptor_notes and dl_note for the method_id.
        '''
        notes = MethodAnalyteVW.objects.filter(method_id__exact=kwargs['method_id']).values('precision_descriptor_notes', 'dl_note').distinct()
        return {'notes' : notes}

    
class BiologicalMethodSummaryView(BaseMethodSummaryView):
    '''Extends the BaseMethodSummaryView to implement the biological method summary page.'''
    
    template_name = 'biological_method_summary.html'
    
class ToxicityMethodSummaryView(BaseMethodSummaryView):
    '''Extends the BaseMethodSummaryView to implement the toxicity method summary page.'''
    
    template_name = 'toxicity_method_summary.html'
    
class StreamPhysicalMethodSummaryView(DetailView):

    template_name = 'stream_physical_method_summary.html'
    context_object_name = 'data'
    model = MethodStgSummaryVw
    
class ExportMethodAnalyte(View, TemplateResponseMixin):
    ''' Extends the standard view. This view creates a
    tab-separated file of the analyte data. Required keyword argument,
    method_id is used to retrieve the analyte information. This uses
    the same query that is used in the MethodSummaryView to retrieve
    the analyte data.
    '''

    def get(self, request, *args, **kwargs):
        '''Processes the get request. The data to export is retrieved from the analyte value
        queryset. A tab separated values file is created.
        '''
        if 'method_id' in kwargs:
            HEADINGS = ('Analyte',
                        'Detection Level',
                        'Bias',
                        'Precision',
                        'Pct False Positive',
                        'Pct False Negative',
                        'Spiking Level')
            qs = _analyte_value_qs(kwargs['method_id'])
        
            response = HttpResponse(mimetype='text/tab-separated-values')
            response['Content-Disposition'] = 'attachment; filename=%s_analytes.tsv' % kwargs['method_id']
            
            response.write('\t'.join(HEADINGS))
            response.write('\n')
            
            for row in qs:
                response.write('%s\t' % row['analyte_name'])
                
                if row['dl_value'] == 999:
                    response.write('N/A\t')
                else:
                    response.write('%.2f %s\t' %(row['dl_value'], row['dl_units']))
                    
                if row['accuracy'] == -999:
                    response.write('N/A\t')
                else:
                    response.write('%d %s\t' %(row['accuracy'], row['accuracy_units']))
                    
                if row['precision'] == 999:
                    response.write('N/A\t')
                else:
                    response.write('%.2f %s\t' %(row['precision'], row['precision_units']))
                    
                if row['false_positive_value'] == None:
                    response.write('\t')
                    
                else:
                    response.write('%s\t' % row['false_positive_value'])
                    
                if row['false_negative_value'] == None:
                    response.write('\t')
                else:
                    response.write('%s\t' % row['false_negative_value'])
                    
                    
                if row['prec_acc_conc_used']:
                    response.write('%.2f %s\t' %(row['prec_acc_conc_used'], row['dl_units']))
                else:
                    response.write('\t')

                response.write('\n')
            
            return response
        
class AddStatisticalSourceView(CreateView):
    template_name = 'create_statistic_source.html'
    form_class = StatisticalSourceEditForm
    model = SourceCitationRef
    
    def get_success_url(self):
        return reverse('search-statistical_source_detail', kwargs={'pk' : self.object.source_citation_id})        
    
    def form_valid(self, form):
        data = form.save(commit=False)
        
        r = SourceCitationRef.objects.aggregate(Max('source_citation_id'))
        data.source_citation_id = r['source_citation_id__max'] + 1
        data.approve_flag = 'F'
        data.citation_type = CitationTypeRef.objects.get(citation_type='Statistic')
        data.insert_person = self.request.user
        
        data.save()
        form.save_m2m()
        
        return HttpResponseRedirect(self.get_success_url())
    
    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(AddStatisticalSourceView, self).dispatch(*args, **kwargs)

class UpdateStatisticalSourceView(UpdateView):
    template_name='update_statistic_source.html'
    form_class = StatisticalSourceEditForm
    model = SourceCitationRef
    
    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(UpdateStatisticalSourceView, self).dispatch(*args, **kwargs)

    def get_success_url(self):
        return reverse('search-statistical_source_detail', kwargs={'pk' : self.object.source_citation_id})            

class StatisticSearchView(SearchResultView, FilterFormMixin):
    
    template_name = 'statistic_search.html'
    form_class = StatisticalSearchForm
    
    def get_qs(self, form):
        qs = SourceCitationRef.objects.filter(citation_type__citation_type__exact='Statistic')
        
        if form.cleaned_data['item_type']:
            qs = qs.filter(item_type__exact=form.cleaned_data['item_type'])
            
        if form.cleaned_data['complexity'] != 'all':
            qs = qs.filter(complexity__exact=form.cleaned_data['complexity'])
            
        if form.cleaned_data['analysis_types']:
            qs = qs.filter(analysis_types__exact=form.cleaned_data['analysis_types'])
            
        if form.cleaned_data['sponser_types']:
            qs = qs.filter(sponser_types__exact=form.cleaned_data['sponser_types'])
            
        if form.cleaned_data['design_objectives']:
            qs = qs.filter(design_objectives__exact=form.cleaned_data['design_objectives'])
            
        if form.cleaned_data['media_emphasized']:
            qs = qs.filter(media_emphasized__exact=form.cleaned_data['media_emphasized'])
            
        if form.cleaned_data['special_topics']:
            qs = qs.filter(special_topics__exact=form.cleaned_data['special_topics'])
            
        return qs
            
    def get_context_data(self, form):
        criteria = []
        criteria.append(_get_criteria_with_name(form, 'item_type'))
        criteria.append(_get_criteria(form['complexity']))
        criteria.append(_get_criteria_with_name(form, 'analysis_types'))
        criteria.append(_get_criteria_with_name(form, 'sponser_types'))
        criteria.append(_get_criteria_with_name(form, 'design_objectives'))
        criteria.append(_get_criteria_with_name(form, 'media_emphasized'))
        criteria.append(_get_criteria_with_name(form, 'special_topics'))
        
        return {'criteria' : criteria}
        
    def get_header_defs(self):
        return None
        
    def get_results_context(self, qs):
        return qs
            
class StatisticalSourceSummaryView(DetailView):
    template_name = 'statistical_source_summary.html'
    
    model = SourceCitationRef
    
    context_object_name = 'data'
    
class StatisticalSourceDetailView(DetailView):
    template_name = 'statistical_source_detail.html'
    
    model = SourceCitationRef
    
    context_object_name = 'data'
