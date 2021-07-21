from datetime import datetime

from django import forms
from django.contrib import admin
from django.contrib import messages
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import connection
from django.db.models import Case, CharField, Count, Q, Value, When
from django.forms.models import BaseInlineFormSet
#Alice added django.forms import Form, Filefield and views
from django.forms import ModelForm, FileField, Form
from django.views.generic import View
from django.http import HttpResponseRedirect
from django.template.defaultfilters import slugify
from django.urls import reverse
from django.urls import path
from django.shortcuts import render
import PyPDF2
import io
from .models import AnalyteMethodJn

from django_object_actions import (
    DjangoObjectActions, takes_instance_or_queryset)

from nemi_project.admin import method_admin
from common import models


class ReadOnlyMixin:
    """
    Since the admin interface does not include read-only functionality, here
    we provide a workaround that may be used with the change view on any
    `ModelAdmin`.

    This mixin will make each field readonly, disable save
    buttons in the template, and disable the save-on-POST.
    """
    def get_readonly_fields(self, request, obj=None):
        # Blunt force, return every field on the model.
        return [field.name for field in self.model._meta.fields]

    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        # This is just to enable the change view in the interface.
        # The rest of the class disables actual change actions.
        # Currently, only admin.
        return request.user.is_superuser

    def change_view(self, request, object_id, form_url='', extra_context=None):
        context = {
            'show_save': False,
            'show_delete_link': False,
            'show_save_as_new': False,
            'show_save_and_add_another': False,
            'show_save_and_continue': False,
        }
        context.update(extra_context or {})

        return super(ReadOnlyMixin, self).change_view(
            request,
            object_id,
            form_url=form_url,
            extra_context=context
        )

    def save_model(self, request, obj, form, change):
        raise PermissionDenied


class PDFFileWidget(admin.widgets.AdminFileWidget):
    template_name = 'common/widgets/pdf_file_input.html'


class PDFFileField(forms.FileField):
    widget = PDFFileWidget

    def clean(self, value, initial=None):
        value = super(PDFFileField, self).clean(value)

        # To validate the PDF, try to read it with PyPDF2.
        if value:
            try:
                PyPDF2.PdfFileReader(value)
                value.seek(0)
            except PyPDF2.utils.PdfReadError:
                raise ValidationError('Please upload a valid PDF file.')

        return value


class RevisionFile:
    def __init__(self, revision, stage):
        self.revision = revision
        self.view_name = {
            'live': 'revision-pdf',
            'online': 'revision-pdf-online',
            'stg': 'revision-pdf-staging',
        }[stage]

    @property
    def url(self):
        return reverse(self.view_name, args=[self.revision.pk])


class AbstractRevisionForm(forms.ModelForm):
    pdf_file = PDFFileField(required=False)

    def __init__(self, *args, **kwargs):
        initial = kwargs.get('initial', {})
        revision = kwargs.get('instance')
        if revision and revision.method_pdf:
            initial['pdf_file'] = RevisionFile(revision, self.STAGE)
        kwargs['initial'] = initial
        super(AbstractRevisionForm, self).__init__(*args, **kwargs)

    def save(self, commit=True):
        instance = super(AbstractRevisionForm, self).save(commit=False)

        if self.cleaned_data['pdf_file']:
            instance.method_pdf = self.cleaned_data['pdf_file'].read()
            instance.mimetype = 'application/pdf'

        if commit:
            instance.save()

        return instance


class RevisionOnlineForm(AbstractRevisionForm):
    STAGE = 'online'
    class Meta:
        model = models.RevisionJoinOnline
        fields = (
            'revision_flag', 'revision_information', 'pdf_file',
            #'reviewer_name'
        )


class RevisionStgForm(AbstractRevisionForm):
    STAGE = 'stg'
    class Meta:
        model = models.RevisionJoinStg
        fields = (
            'revision_flag', 'revision_information', 'pdf_file',
            #'reviewer_name'
        )


class RevisionInlineFormSet(BaseInlineFormSet):
    fieldsets = (
        (None, {
            'fields': ('revision_flag', 'revision_information', 'source_citation')
        })
    )

    def clean(self):
        super(RevisionInlineFormSet, self).clean()

        # If more than one revision has `revision_flag` set, error.
        if sum(f.cleaned_data.get('revision_flag') or 0 for f in self.forms) > 1:
            msg = 'There may not be more than one active revision per method.'
            raise ValidationError(msg)


class AbstractRevisionInline(ReadOnlyMixin, admin.TabularInline):
    extra = 0
    formset = RevisionInlineFormSet
    class Meta:
        abstract = True


class AbstractEditableRevisionInline(AbstractRevisionInline):
    fields = ('revision_flag', 'revision_information', 'pdf_file')
    class Meta:
        abstract = True

    def pdf_file(self):
        # If we have a method_pdf, use the revision name as the PDF label.
        return '%s.pdf' % self.revision_information if self.method_pdf else None

    def save_model(self, request, obj, form, change):
        if not change:
            obj.insert_person_name = request.user.username
        obj.last_update_person_name = request.user.username
        return super(AbstractEditableRevisionInline, self).save_model(request, obj, form, change)

    def get_readonly_fields(self, request, obj=None):
        # Owners can edit any field when in the "online" tables.
        # if obj and obj.insert_person_name == request.user.username:
        #     return ()
        # return super(AbstractEditableRevisionInline, self).get_readonly_fields(request, obj=obj)

        # For now, allow any admin to edit the online and staging tables.
        return ()

    def has_add_permission(self, request, obj=None):
        # As an inline, we defer to the parent permissions
        return True

    def has_change_permission(self, request, obj=None):
        # As an inline, we defer to the parent permissions
        return True

    def has_delete_permission(self, request, obj=None):
        return True


class RevisionOnlineAdmin(AbstractEditableRevisionInline):
    model = models.RevisionJoinOnline
    form = RevisionOnlineForm


class RevisionStgAdmin(AbstractEditableRevisionInline):
    model = models.RevisionJoinStg
    form = RevisionStgForm


class ProtocolRevisionStgAdmin(AbstractEditableRevisionInline):
    model = models.ProtocolRevisionJoinStg
    form = RevisionStgForm


class RevisionAdmin(AbstractRevisionInline):
    model = models.RevisionJoin
    readonly_fields = (
        'mimetype', 'revision_flag', 'revision_information', 'insert_date',
        'insert_person_name', 'last_update_date', 'last_update_person_name',
        'pdf_insert_person', 'pdf_insert_date', 'source_citation',
        'date_loaded', 'revision_pdf_url')

    def revision_pdf_url(self, obj):
        if not obj.pk:
            return ''
        return '<a href="%s">Download PDF</a>' % reverse('revision-pdf',
                                                         args=[obj.pk])

    revision_pdf_url.allow_tags = True

    def get_readonly_fields(self, request, obj=None):
        return self.readonly_fields


class AbstractAnalyteMethodAdmin(admin.StackedInline):
    fieldsets = (
        (None, {
            'fields': (
                ('analyte',),
                ('dl_value', 'dl_units'),
                ('accuracy', 'accuracy_units'),
                ('false_positive_value', 'false_negative_value'),
                ('precision', 'precision_units', 'prec_acc_conc_used'),
            ),
        }),
        (None, {
            'fields': (
                ('insert_date', 'insert_person_name'),
                ('last_update_date', 'last_update_person_name'),
            ),
        }),
        (None, {
            'fields': (
                ('green_flag', 'yellow_flag', 'confirmatory'),
            ),
        }),
    )
    readonly_fields = (
        'insert_date', 'insert_person_name', 'last_update_date',
        'last_update_person_name', 'green_flag', 'yellow_flag', 'confirmatory'
    )
    raw_id_fields = ('analyte',)
    extra = 0
    class Meta:
        abstract = True

    def save_model(self, request, obj, form, change):
        obj.last_update_date = datetime.now()
        obj.last_update_person_name = request.user.username
        if not obj.pk:
            obj.insert_person_name = obj.last_update_person_name
            obj.insert_date = obj.last_update_date

        super(AbstractAnalyteMethodAdmin, self).save_model(
            request, obj, form, change)


class AnalyteMethodOnlineAdmin(AbstractAnalyteMethodAdmin):
    model = models.AnalyteMethodJnOnline


class AnalyteMethodStgAdmin(AbstractAnalyteMethodAdmin):
    model = models.AnalyteMethodJnStg


class AnalyteMethodAdmin(ReadOnlyMixin, AbstractAnalyteMethodAdmin):
    model = models.AnalyteMethodJn


class ActiveRevisionCountFilter(admin.SimpleListFilter):
    title = 'active revision count'
    parameter_name = 'active_revision_count'

    def lookups(self, request, model_admin):
        return (
            (0, 'None'),
            (1, 'One'),
            (2, 'More than one')
        )

    def queryset(self, request, queryset):
        try:
            value = int(self.value())
        except TypeError:
            return queryset

        if value > 1:
            return queryset.filter(active_revision_count__gt=1)

        return queryset.filter(active_revision_count=value)


def list_q_filter(label, q_object):
    class ListQFilter(admin.SimpleListFilter):
        title = label
        parameter_name = slugify(label)

        def lookups(self, request, model_admin):
            return (
                ('1', 'Yes'),
                ('0', 'No'),
            )

        def queryset(self, request, queryset):
            if self.value() == '1':
                return queryset.filter(q_object)
            elif self.value() == '0':
                return queryset.filter(~q_object)

            return queryset

    return ListQFilter


class SourceCitationAdmin(ReadOnlyMixin, admin.ModelAdmin):
    search_fields = (
        'source_citation', 'source_citation_name',
        'title', 'source_citation_information',
    )
    list_display = (
        'source_citation', 'source_citation_name',
        'title', 'source_citation_information'
    )
    ordering = ('source_citation',)

    def get_queryset(self, request):
        queryset = super(SourceCitationAdmin, self).get_queryset(request)
        return queryset.filter(citation_type='METHOD')

    def get_model_perms(self, request):
        """
        Return empty perms dict, thus hiding the model from admin index.
        """
        return {}


class AbstractMethodAdmin(admin.ModelAdmin):
    class Meta:
        abstract = True

    def method_identifier(self, obj):
        return '{0}: {1}'.format(obj.method_source, obj.source_method_identifier)

    list_display = (
        'method_identifier', 'method_official_name', 'insert_date', 'last_update_date',
        'active_revision_count', 'analyte_count'
    )
    list_filter = (
        ActiveRevisionCountFilter,
        list_q_filter(
            'active revision has PDF',
            Q(revisions__revision_flag=True) and Q(
                revisions__method_pdf__isnull=False)
        ),
        list_q_filter(
            'has analytes',
            Q(analyte_count__gt=0)
        ),
        'insert_person_name', 'insert_date'
    )
    fieldsets = (
        ('General Fields', {
            #'classes': ('collapse',),
            'fields': (
                'source_method_identifier', 'method_descriptive_name',
                'method_type', 'method_subcategory',
                'method_source', 'source_citation', 'brief_method_summary',
                'media_name', 'method_official_name', 'instrumentation',
                'waterbody_type', 'scope_and_application', 'dl_type',
                'dl_note',
                ('applicable_conc_range', 'conc_range_units',),
                'interferences', 'precision_descriptor_notes',
                'qc_requirements', 'sample_handling', 'max_holding_time',
                'sample_prep_methods', 'relative_cost',
                'link_to_full_method', 'regs_only', 'reviewer_name',
            ),
        }),
        ('CBR-only fields', {
            'fields': (('rapidity', 'screening', 'cbr_only'),)
        }),
        ('Greenness profile fields', {
            'fields': (
                ('collected_sample_amt_ml', 'collected_sample_amt_g'),
                ('analysis_amt_ml', 'analysis_amt_g'),
                'liquid_sample_flag', 'ph_of_analytical_sample', 'calc_waste_amt',
                'quality_review_id', 'pbt', 'toxic', 'corrosive', 'waste',
                'assumptions_comments',
            )
        }),
        ('Biological assessment fields', {
            'fields': (
                'index_period',
                'field_or_lab',
                'mesh_size',
                'sampling_reach_length',
                'habitats_sampled',
                'num_subsamples_composited',
                'target_num_organisms',
                'total_sampling_area',
                'field_preservative',
                'taxa_included',
                'laboratory_subsample',
                'large_rare_pick'
            )
        })
    )
    raw_id_fields = ('source_citation',)

    def formfield_for_dbfield(self, db_field, **kwargs):
        field = super(AbstractMethodAdmin, self).formfield_for_dbfield(
            db_field, **kwargs)

        # Make fields required here rather than in DB models, so the
        # statistical method forms' functionality won't be impacted.
        if db_field.name in (
                'method_subcategory', 'media_name', 'method_source',
                'method_descriptive_name'):
            field.required = True

        if db_field.name in (
                'method_descriptive_name', 'brief_method_summary',
                'method_official_name', 'scope_and_application', 'dl_note',
                'applicable_conc_range', 'interferences',
                'precision_descriptor_notes', 'qc_requirements',
                'sample_handling', 'sample_prep_methods',
                'assumptions_comments'):
            field.widget.attrs['rows'] = 4
            field.widget = forms.Textarea(attrs=field.widget.attrs)

        return field

    def get_queryset(self, request):
        queryset = super(AbstractMethodAdmin, self).get_queryset(request)

        # Add annotation for the count of active revisions, the number of
        # analytes per method, and the completion status of the method.
        queryset = queryset.annotate(
            active_revision_count=Count(Case(When(
                revisions__revision_flag=True,
                then=1
            ))),
            analyte_count=Count('analytes'),
        )

        return queryset

    def active_revision_count(self, obj):
        return obj.active_revision_count

    def analyte_count(self, obj):
        return obj.analyte_count

    def has_module_permission(self, request):
        # For now, only admins have access
        return request.user.is_superuser

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def method_is_valid(self, method):
        return method.completion_status.startswith('COMPLETE')


class AbstractEditableMethodAdmin(AbstractMethodAdmin):
    list_display = AbstractMethodAdmin.list_display + ('completion_status',)
    list_filter = (
        list_q_filter(
            'completion status',
            Q(completion_status__startswith='COMPLETE')
        ),
    ) + AbstractMethodAdmin.list_filter

    def get_queryset(self, request):
        queryset = super(AbstractEditableMethodAdmin, self).get_queryset(request)

        # Add the completion status of the method.
        return queryset.annotate(
            completion_status=Case(
                When(
                    active_revision_count=1,
                    analyte_count__gt=0,
                    then=Value('COMPLETE')),
                When(
                    active_revision_count=1,
                    analyte_count=0,
                    no_analyte_flag='Y',
                    then=Value('COMPLETE')),
                When(
                    active_revision_count__gt=1,
                    then=Value('INCOMPLETE - More than one active revision')),
                When(
                    active_revision_count=0,
                    analyte_count=0,
                    then=Value('INCOMPLETE - Needs analytes and revision')),
                When(
                    active_revision_count=0,
                    then=Value('INCOMPLETE - Needs a revision')),
                When(
                    analyte_count=0,
                    then=Value('INCOMPLETE - Needs an analyte')),
                default=Value('UNKNOWN'),
                output_field=CharField()
            )
        )

    def completion_status(self, obj):
        return obj.completion_status


class MethodOnlineAdmin(DjangoObjectActions, AbstractEditableMethodAdmin):
    class Meta:
        model = models.MethodOnline

    list_filter = AbstractEditableMethodAdmin.list_filter
    inlines = (AnalyteMethodOnlineAdmin, RevisionOnlineAdmin)
    actions = ('submit_for_review','analyte_bulk_load',)
    change_actions = actions
    fieldsets = (
        ('Submission-Specific Fields', {
            'fields': (
                ('no_analyte_flag',),
                #('ready_for_review', 'delete_after_load'),
                ('comments',),
            )
        }),
    ) + AbstractEditableMethodAdmin.fieldsets
    ordering = ('-last_update_date',)

    def get_queryset(self, request):
        queryset = super(MethodOnlineAdmin, self).get_queryset(request)
        return queryset.filter(ready_for_review='N')

    def formfield_for_dbfield(self, db_field, **kwargs):
        field = super(MethodOnlineAdmin, self).formfield_for_dbfield(
            db_field, **kwargs)

        if db_field.name in ('comments',):
            field.widget.attrs['rows'] = 4
            field.widget = forms.Textarea(attrs=field.widget.attrs)

        return field

    def has_add_permission(self, request, obj=None):
        # For now, only admins have acesss.
        return request.user.is_superuser

    def has_change_permission(self, request, obj=None):
        # Users may edit their own submissions, if it hasn't already been
        # submitted for review.
        # Currently, assume only admin users use the system.
        return request.user.is_superuser

    def has_delete_permission(self, request, obj=None):
        # For now, only admins have acesss.
        return request.user.is_superuser

    @takes_instance_or_queryset
    def submit_for_review(self, request, queryset):
        # If any of the methods are incomplete, bail.
        if any(not self.method_is_valid(method) for method in queryset):
            self.message_user(
                request,
                'Not submitted: Method is missing analytes or revisions.',
                level=messages.ERROR
            )
            return

        # Mark all methods as ready for review
        rows_updated = queryset.update(ready_for_review='Y', approved='N')

        # Redirect back to the list page and notify user of success.
        self.message_user(request, 'submitted %d method%s for review' % (
            rows_updated, 's' if rows_updated > 1 else ''))
        return HttpResponseRedirect(
            reverse('method_admin:common_methodonline_changelist')
        )

    submit_for_review.label = 'Submit for review'
    submit_for_review.short_description = 'Submit method for review'

    def analyte_bulk_load(self, request, queryset):

        # Redirect to analyte bulk loading page.
        return HttpResponseRedirect(
            'method_admin:upload_csv'
        )

    analyte_bulk_load.label = 'Bulk upload Analytes'
    analyte_bulk_load.short_description = 'Redirect to page for uploading multiple analyte records'


    def save_model(self, request, obj, form, change):
        # If adding a new instance, set `insert_person_name` to current user.
        if not change:
            obj.insert_person_name = request.user.username
        return super(MethodOnlineAdmin, self).save_model(request, obj, form, change)

    def get_readonly_fields(self, request, obj=None):
        # Owners can edit any field when in the "online" tables.
        if obj and obj.insert_person_name == request.user.username:
            return ()
        return super(MethodOnlineAdmin, self).get_readonly_fields(request, obj=obj)

    def get_urls(self):
        urls = super().get_urls()
        new_urls = [path('upload_csv/', self.upload_csv),]
        return new_urls + urls

    def upload_csv(self, request):

        if request.method == "POST":
            print("action is post")
            csv_file = request.FILES["csv_upload"]

            file_data = csv_file.read().decode("utf-8")
            #csv_data = file_data.split("\n")
            csv_data = io.StringIO(file_data)

            for x in csv_data:
                fields = x.split(",")
                print(repr(fields))
                print(fields[0],fields[1])
                created = AnalyteMethodJn.objects.update_or_create(
                    analyte_method_id = 99999985740,
                    method_id = 4827,
                    analyte_id = 18178,
                    dl_value = 0.02,
                    dl_units = 'pH',
                    )

        form = csv_import_form()
        data = {"form": form}
        return render(request, "admin/bulk_upload.html", data)

class MethodStgAdmin(DjangoObjectActions, AbstractEditableMethodAdmin):
    class Meta:
        model = models.MethodStg

    list_display = AbstractEditableMethodAdmin.list_display + (
        'approved', 'approved_date')
    list_filter = (
        'approved', 'approved_date'
    ) + AbstractEditableMethodAdmin.list_filter
    inlines = (AnalyteMethodStgAdmin, RevisionStgAdmin)
    actions = ('publish', 'archive')
    change_actions = actions
    fieldsets = (
        ('Review-Specific Fields', {
            'fields': (
                ('no_analyte_flag',),
            )
        }),
    ) + AbstractEditableMethodAdmin.fieldsets
    ordering = ('-last_update_date',)

    @takes_instance_or_queryset
    def publish(self, request, queryset):
        rows_updated = queryset.update(approved='Y')
        self.message_user(request, 'published %d method%s' % (
            rows_updated, 's' if rows_updated > 1 else ''))

    publish.label = 'Publish'
    publish.short_description = 'Publish the selected methods'

    @takes_instance_or_queryset
    def archive(self, request, queryset):
        method_ids = queryset.values_list('method_id', flat=True)
        try:
            cursor = connection.cursor()
            for method_id in method_ids:
                cursor.callproc(
                    'archive_method', [
                        method_id,
                        'Y',  # DELETE_FLAG - remove from staging and production
                        'Y',  # PUBLIC_FLAG - method should be public
                    ]
                )
        finally:
            cursor.close()

        rows_updated = len(method_ids)
        self.message_user(request, 'archived %d method%s' % (
            rows_updated, 's' if rows_updated > 1 else ''))

    archive.label = 'Archive'
    archive.short_description = 'Archive the selected methods'

    def has_add_permission(self, request, obj=None):
        # For now, only admins have acesss.
        return request.user.is_superuser

    def has_change_permission(self, request, obj=None):
        # Admin may only edit staging methods
        return request.user.is_superuser

    def has_delete_permission(self, request, obj=None):
        # For now, only admins have acesss.
        return request.user.is_superuser


class MethodAdmin(ReadOnlyMixin, AbstractMethodAdmin):
    class Meta:
        model = models.Method

    inlines = (AnalyteMethodAdmin, RevisionAdmin)

    def has_delete_permission(self, request, obj=None):
        # For now, only admins have acesss.
        return request.user.is_superuser


class ProtocolMethodInlineAdmin(admin.TabularInline):
    model = models.ProtocolMethodStgRel
    extra = 0
    raw_id_fields = ('method',)


class ProtocolSourceCitationAdmin(DjangoObjectActions, admin.ModelAdmin):
    inlines = (ProtocolMethodInlineAdmin, ProtocolRevisionStgAdmin)
    list_display = (
        'source_citation', 'source_citation_name',
        'source_citation_information', 'insert_person_name', 'insert_date',
        'update_date', 'title', 'author', 'publication_year',
        'ready_for_review', 'approved', 'approved_date'
    )
    fieldsets = (
        (None, {
            'fields': (
                ('insert_person_name',),
                ('insert_date', 'update_date'),
                ('ready_for_review',),
                ('approved', 'approved_date'),
            ),
        }),
        (None, {
            'fields': (
                'source_citation', 'source_citation_name',
                'source_citation_information', 'title', 'author',
                'abstract_summary', 'table_of_contents', 'publication_year',
                'link', 'notes',
            ),
        }),
    )
    readonly_fields = (
        'insert_person_name', 'insert_date', 'update_date', 'ready_for_review',
        'approved', 'approved_date'
    )
    actions = ('submit_for_review', 'approve_protocol')
    ordering = ('-update_date',)
    change_actions = actions

    def get_queryset(self, request):
        queryset = super(ProtocolSourceCitationAdmin, self).get_queryset(request)
        return queryset.filter(citation_type='PROTOCOL')

    def formfield_for_dbfield(self, db_field, **kwargs):
        field = super(ProtocolSourceCitationAdmin, self).formfield_for_dbfield(
            db_field, **kwargs)

        if db_field.name in ('source_citation', 'source_citation_name',
                             'source_citation_information', 'title', 'author',
                             'abstract_summary', 'publication_year'):
            field.required = True

        if db_field.name in ('source_citation_information', 'title', 'author',
                             'abstract_summary', 'table_of_contents', 'notes'):
            field.widget = forms.Textarea(attrs=field.widget.attrs)

        return field

    @takes_instance_or_queryset
    def submit_for_review(self, request, queryset):
        rows_updated = queryset.update(ready_for_review='Y', approved='N')
        self.message_user(request, 'submitted %d protocol%s for review' % (
            rows_updated, 's' if rows_updated > 1 else ''))

    submit_for_review.label = 'Submit for review'
    submit_for_review.short_description = 'Submit this protocol for review'

    @takes_instance_or_queryset
    def approve_protocol(self, request, queryset):
        rows_updated = queryset.update(approved='Y', approved_date=datetime.now())
        self.message_user(request, 'approved %d protocol%s' % (
            rows_updated, 's' if rows_updated > 1 else ''))

    approve_protocol.label = 'Approve'
    approve_protocol.short_description = 'Approve and publish this protocol'

    def save_model(self, request, obj, form, change):
        obj.citation_type = 'PROTOCOL'

        obj.update_date = obj.approved_date
        if not obj.pk:
            obj.insert_person_name = request.user.username
            obj.insert_date = obj.update_date

        # Save to the staging table
        super(ProtocolSourceCitationAdmin, self).save_model(
            request, obj, form, change)

    def has_delete_permission(self, request, *args, **kwargs):
        return False

      #copy pasted for bulk loading code

    # end of copy paste for bulk loading code
class csv_import_form(Form):
    csv_upload = forms.FileField()

method_admin.register(models.MethodOnline, MethodOnlineAdmin)
method_admin.register(models.MethodStg, MethodStgAdmin)
method_admin.register(models.Method, MethodAdmin)
method_admin.register(models.ProtocolSourceCitationStgRef, ProtocolSourceCitationAdmin)
method_admin.register(models.SourceCitationRef, SourceCitationAdmin)