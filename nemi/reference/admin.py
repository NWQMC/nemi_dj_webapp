from datetime import datetime

from django import forms
from django.contrib import admin
from django.forms import model_to_dict
from django_object_actions import (
    DjangoObjectActions, takes_instance_or_queryset)
from tinymce.widgets import TinyMCE

from nemi_project.admin import method_admin

from . import models


class AbstractMethodAdmin(admin.ModelAdmin):
    class Meta:
        abstract = True

    def is_method_admin(self, request, *args, **kwargs):
        if not hasattr(self, '_admin'):
            self._is_admin = request.user.groups.filter(
                name='method_admin').exists()
        return self._is_admin

    has_module_permission = is_method_admin
    has_add_permission = is_method_admin
    has_change_permission = is_method_admin

    def has_delete_permission(self, request, *args, **kwargs):
        return False


class AbstractReferenceAdmin(AbstractMethodAdmin):
    class Meta:
        abstract = True

    fieldsets = (
        (None, {
            'fields': (
                ('data_entry_name', 'data_entry_date'),
                ('update_name', 'update_date'),
            ),
        }),
    )
    readonly_fields = (
        'data_entry_name', 'data_entry_date', 'update_name', 'update_date'
    )

    def audit_instance(self, username, obj):
        obj.update_name = username
        obj.update_date = datetime.now()
        if not obj.pk:
            obj.data_entry_name = username
            obj.data_entry_date = obj.update_date

    def save_model(self, request, obj, form, change):
        self.audit_instance(request.user.username, obj)
        return super(AbstractReferenceAdmin, self).save_model(request, obj, form, change)


class AccuracyUnitsDomAdmin(AbstractReferenceAdmin):
    list_display = (
        'accuracy_units', 'accuracy_units_description'
    ) + AbstractReferenceAdmin.readonly_fields
    fieldsets = (
        (None, {
            'fields': (
                'accuracy_units',
                'accuracy_units_description',
            ),
        }),
    ) + AbstractReferenceAdmin.fieldsets


class AnalyteCodeRelAdmin(admin.TabularInline):
    model = models.AnalyteCodeRel
    extra = 0
    fields = ('analyte_name', 'preferred') + AbstractReferenceAdmin.readonly_fields
    readonly_fields = AbstractReferenceAdmin.readonly_fields

    def save_model(self, request, obj, form, change):
        self.audit_instance(request, obj, change)
        return super(AnalyteCodeRelAdmin, self).save_model(request, obj, form, change)


class AnalyteRefAdmin(AbstractReferenceAdmin):
    inlines = (AnalyteCodeRelAdmin,)
    list_display = ('analyte_code', 'analyte_type', 'analyte_cbr')
    fieldsets = (
        (None, {
            'fields': (
                'analyte_code', 'analyte_type', 'analyte_cbr', 'usgs_pcode',
                'analyte_code_cbr',
                # These two are in the database but not in the APEX UI:
                #'cbr_analyte_category', 'cbr_analyte_intro'
            ),
        }),
    ) + AbstractReferenceAdmin.fieldsets

    def save_model(self, request, obj, form, change):
        self.audit_instance(request.user.username, obj)
        return super(AnalyteRefAdmin, self).save_model(request, obj, form, change)

    def save_formset(self, request, form, formset, change):
        instances = formset.save(commit=False)
        for instance in formset.deleted_objects:
            instance.delete()
        for instance in instances:
            self.audit_instance(request.user.username, instance)
            instance.save()
        formset.save_m2m()


class DlRefAdmin(AbstractReferenceAdmin):
    list_display = (
        'dl_type_id', 'dl_type', 'dl_type_description'
    ) + AbstractReferenceAdmin.readonly_fields
    fieldsets = (
        (None, {
            'fields': (
                'dl_type', 'dl_type_description'
            ),
        }),
    ) + AbstractReferenceAdmin.fieldsets
    ordering = ('dl_type_id',)


class DlUnitsDomAdmin(AbstractReferenceAdmin):
    list_display = (
        'dl_units', 'dl_units_description') + AbstractReferenceAdmin.readonly_fields
    fieldsets = (
        (None, {
            'fields': (
                'dl_units', 'dl_units_description'
            ),
        }),
    ) + AbstractReferenceAdmin.fieldsets

    def get_readonly_fields(self, request, obj=None):
        readonly_fields = AbstractReferenceAdmin.readonly_fields
        # If we're editing, don't allow changing the primary key
        if obj:
            readonly_fields += ('dl_units',)
        return readonly_fields


class InstrumentationRefAdmin(AbstractReferenceAdmin):
    list_display = (
        'instrumentation', 'instrumentation_description'
    ) + AbstractReferenceAdmin.readonly_fields
    fieldsets = (
        (None, {
            'fields': (
                'instrumentation', 'instrumentation_description'
            ),
        }),
    ) + AbstractReferenceAdmin.fieldsets


class MethodSourceRefForm(forms.ModelForm):
    class Meta:
        model = models.MethodSourceRef
        fields = '__all__'
        widgets = {
            'method_source_contact': TinyMCE(attrs={'cols': 100, 'rows': 50})
        }


class MethodSourceRefAdmin(AbstractReferenceAdmin):
    form = MethodSourceRefForm
    list_display = (
        'method_source', 'method_source_url', 'method_source_name',
        'method_source_contact', 'method_source_email'
    ) + AbstractReferenceAdmin.readonly_fields
    fieldsets = (
        (None, {
            'fields': (
                'method_source', 'method_source_url', 'method_source_name',
                'method_source_contact', 'method_source_email'
            ),
        }),
    ) + AbstractReferenceAdmin.fieldsets


class ClassicSourceCitationAdmin(AbstractMethodAdmin):
    list_display = (
        'source_citation', 'source_citation_name',
        'source_citation_information', 'insert_person_name', 'insert_date',
        'update_date'
    )
    fields = (
        'source_citation', 'source_citation_name',
        'source_citation_information'
    )

    def get_queryset(self, request):
        queryset = super(ClassicSourceCitationAdmin, self).get_queryset(request)
        return queryset.filter(citation_type='METHOD')

    def formfield_for_dbfield(self, db_field, **kwargs):
        field = super(ClassicSourceCitationAdmin, self).formfield_for_dbfield(
            db_field, **kwargs)

        # Multi-line widget for CharFields:
        if db_field.name in ('source_citation_name',
                             'source_citation_information'):
            field.widget = forms.Textarea(attrs=field.widget.attrs)

        return field

    def save_model(self, request, obj, form, change):
        obj.citation_type = 'METHOD'
        obj.approved = 'Y'
        obj.approved_date = datetime.now()

        obj.update_date = obj.approved_date
        if not obj.pk:
            obj.insert_person_name = request.user.username
            obj.insert_date = obj.update_date

        # Save to the staging table
        super(ClassicSourceCitationAdmin, self).save_model(
            request, obj, form, change)

        # Save a copy to the live table
        values = model_to_dict(obj)
        source_citation_id = values.pop('source_citation_id')
        values['item_type_id'] = values.pop('item_type')
        values.pop('owner_editable')
        values.pop('ready_for_review')
        models.SourceCitationRef.objects.update_or_create(
            source_citation_id=source_citation_id,
            defaults=values
        )


class ProtocolMethodInlineAdmin(admin.TabularInline):
    model = models.ProtocolMethodStgRel
    extra = 0
    raw_id_fields = ('method',)


class ProtocolSourceCitationAdmin(DjangoObjectActions, AbstractMethodAdmin):
    inlines = (ProtocolMethodInlineAdmin,)
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
        rows_updated = queryset.update(ready_for_review='Y')
        self.message_user(request, 'submitted %d protocol%s for review' % (
            rows_updated, 's' if rows_updated > 1 else ''))

    submit_for_review.label = 'Submit for review'
    submit_for_review.short_description = 'Submit this protocol for review'

    @takes_instance_or_queryset
    def approve_protocol(self, request, queryset):
        rows_updated = queryset.update(approved='Y', approved_date=datetime.now())
        self.message_user(request, 'submitted %d protocol%s for review' % (
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


method_admin.register(models.AccuracyUnitsDom, AccuracyUnitsDomAdmin)
method_admin.register(models.AnalyteRef, AnalyteRefAdmin)
method_admin.register(models.DlRef, DlRefAdmin)
method_admin.register(models.DlUnitsDom, DlUnitsDomAdmin)
method_admin.register(models.InstrumentationRef, InstrumentationRefAdmin)
method_admin.register(models.MethodSourceRef, MethodSourceRefAdmin)
method_admin.register(models.ClassicSourceCitationStgRef, ClassicSourceCitationAdmin)
method_admin.register(models.ProtocolSourceCitationStgRef, ProtocolSourceCitationAdmin)
