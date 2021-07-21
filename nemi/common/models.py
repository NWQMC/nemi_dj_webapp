from django.contrib.auth.models import User
from django.db import models

from reference import models as refs


class DefinitionsDOM(models.Model):

    definition_name = models.CharField(max_length=75, primary_key=True)
    definition_description = models.CharField(max_length=1500)
    definition_abbrev = models.CharField(max_length=30)
    web_desc_bio = models.CharField(max_length=4000, blank=True)
    web_desc_all = models.CharField(max_length=4000, blank=True)
    web_desc_phys = models.CharField(max_length=4000, blank=True)
    column_help = models.CharField(max_length=4000, blank=True)

    class Meta:
        db_table = 'definitions_dom'
        managed = False

    def __str__(self):
        return self.definition_name


class MethodSubcategoryRef(models.Model):

    method_subcategory_id = models.IntegerField(primary_key=True)
    method_category = models.CharField(max_length=50)
    method_subcategory = models.CharField(max_length=40)

    class Meta:
        db_table = 'method_subcategory_ref'
        managed = False
        ordering = ('method_subcategory',)

    def __str__(self):
        return self.method_subcategory


class MethodSourceRef(models.Model):

    method_source_id = models.IntegerField(primary_key=True)
    method_source = models.CharField(max_length=20)
    method_source_url = models.CharField(max_length=200, blank=True)
    method_source_name = models.CharField(max_length=150)
    method_source_contact = models.CharField(max_length=450, blank=True)
    method_source_email = models.CharField(max_length=100, blank=True)

    class Meta:
        db_table = 'method_source_ref'
        managed = False
        ordering = ['method_source']

    def __str__(self):
        return self.method_source


class StatisticalItemType(models.Model):

    stat_item_index = models.IntegerField(primary_key=True)
    item = models.CharField(max_length=100)

    class Meta:
        db_table = 'statistical_item_type'
        ordering = ['item']
        managed = False

    def __str__(self):
        return self.item


class StatisticalMediaNameManager(models.Manager):
    '''Extends the Manager class to provide a query set that returns valid media for statistical methods.
    '''

    def get_queryset(self):
        return super(StatisticalMediaNameManager, self).get_queryset().exclude(
            media_name__iexact='Various').exclude(media_name__iexact='Water').exclude(media_name__iexact='Sediment')


class MediaNameDOM(models.Model):

    media_name = models.CharField(primary_key=True, max_length=30)
    media_id = models.IntegerField()

    objects = models.Manager()
    stat_media = StatisticalMediaNameManager()

    class Meta:
        db_table = 'media_name_dom'
        ordering = ['media_name']
        managed = False

    def __str__(self):
        return self.media_name.lower().title()


class StatisticalSourceType(models.Model):

    stat_source_index = models.IntegerField(primary_key=True)
    source = models.CharField(max_length=100)

    class Meta:
        db_table = 'statistical_source_type'
        ordering = ['source']
        managed = False

    def __str__(self):
        return self.source


class SourceCitationRefAbstract(models.Model):
    ''' Abstract model which abstracts the common fields for the three flavors of source citation ref tables.'''

    source_citation = models.CharField(max_length=30)
    source_citation_name = models.CharField(max_length=450)
    source_citation_information = models.CharField(max_length=1500,
                                                   blank=True)
    title = models.CharField(max_length=450)
    author = models.CharField(max_length=450)
    table_of_contents = models.CharField(max_length=1000)
    abstract_summary = models.CharField(max_length=2000)
    link = models.URLField(max_length=450, blank=True)
    publication_year = models.IntegerField(null=True)
    country = models.CharField(max_length=100, blank=True)
    item_type = models.ForeignKey(StatisticalItemType, models.CASCADE)
    item_type_note = models.CharField(max_length=50,
                                      blank=True)
    sponser_type_note = models.CharField(max_length=50,
                                         blank=True)
    citation_type = models.CharField(max_length=50,
                                     blank=True)
    insert_date = models.DateField(auto_now_add=True)
    update_date = models.DateField(auto_now=True)
    insert_person_name = models.CharField(max_length=50,
                                          blank=True)

    class Meta:
        abstract = True
        ordering = ('source_citation',)

    def __str__(self):
        return self.source_citation


class SourceCitationOnlineRef(SourceCitationRefAbstract):

    source_citation_id = models.AutoField(primary_key=True)

    class Meta:
        db_table = 'source_citation_online_ref'
        managed = False


class SourceCitationStgRef(SourceCitationRefAbstract):

    source_citation_id = models.IntegerField(primary_key=True)

    class Meta:
        db_table = 'source_citation_stg_ref'
        managed = False


class ProtocolSourceCitationManager(models.Manager):
    def get_queryset(self):
        return super(ProtocolSourceCitationManager, self).get_queryset().filter(citation_type='PROTOCOL')


class SourceCitationRef(SourceCitationRefAbstract):

    source_citation_id = models.IntegerField(primary_key=True)

    objects = models.Manager()
    protocol_objects = ProtocolSourceCitationManager()

    class Meta:
        db_table = 'source_citation_ref'
        managed = False


class PublicationSourceRelAbstract(models.Model):

    source = models.ForeignKey(StatisticalSourceType,
                               models.DO_NOTHING,
                               db_column='statisticalsourcetype_id')

    class Meta:
        abstract = True

    def __str__(self):
        return str(self.source)


class PublicationSourceRelStg(PublicationSourceRelAbstract):

    source_citation_ref_id = models.IntegerField(db_column='sourcecitationref_id')

    class Meta:
        db_table = 'publication_source_rel_stg'
        ordering = ['source']
        managed = False


class PublicationSourceRel(PublicationSourceRelAbstract):

    source_citation_ref = models.ForeignKey(SourceCitationRef,
                                            models.CASCADE,
                                            db_column='sourcecitationref_id')

    class Meta:
        db_table = 'publication_source_rel'
        ordering = ['source']
        managed = False


class DlRef(models.Model):

    dl_type_id = models.IntegerField(primary_key=True, unique=True)
    dl_type = models.CharField(max_length=11, unique=True)
    dl_type_description = models.CharField(max_length=50, unique=True)

    class Meta:
        db_table = 'dl_ref'
        managed = False
        ordering = ('dl_type',)

    def __str__(self):
        return self.dl_type


class DlUnitsDom(models.Model):

    dl_units = models.CharField(max_length=20, primary_key=True, unique=True)
    dl_units_description = models.CharField(max_length=60, blank=True)

    class Meta:
        db_table = 'dl_units_dom'
        managed = False
        ordering = ('dl_units',)

    def __str__(self):
        return self.dl_units


class RelativeCostRef(models.Model):

    relative_cost_id = models.IntegerField(primary_key=True)
    relative_cost_symbol = models.CharField(max_length=7)
    relative_cost = models.CharField(max_length=40)
    cost_effort_key = models.CharField(max_length=10)

    class Meta:
        db_table = 'relative_cost_ref'
        managed = False

    def __str__(self):
        return self.relative_cost


class InstrumentationRef(models.Model):

    instrumentation_id = models.IntegerField(primary_key=True)
    instrumentation = models.CharField(max_length=20)
    instrumentation_description = models.CharField(max_length=200)

    class Meta:
        db_table = 'instrumentation_ref'
        managed = False
        ordering = ('instrumentation_description',)

    def __str__(self):
        return self.instrumentation_description


class WaterbodyTypeRef(models.Model):

    # This table is unusual, in that the primary key is waterbody_type_id,
    # but we reference it via waterbody_type_desc in the Method tables.
    # So we cheat a bit, and treat `waterbody_type_desc` as the primary key.

    # Columns, as reflected by inspectdb:
    #waterbody_type_id = models.IntegerField(unique=True, primary_key=True)
    #waterbody_type_desc = models.CharField(max_length=100, unique=True)

    waterbody_type_id = models.IntegerField(unique=True)
    waterbody_type_desc = models.CharField(
        primary_key=True, max_length=100, unique=True)

    class Meta:
        db_table = 'waterbody_type_ref'
        managed = False

    def __str__(self):
        return self.waterbody_type_desc


class MethodTypeRef(models.Model):

    method_type_id = models.IntegerField(primary_key=True)
    method_type_desc = models.CharField(max_length=100)

    class Meta:
        db_table = 'method_type_ref'
        managed = False

    def __str__(self):
        return self.method_type_desc


COMPLEXITY_CHOICES = [
    ('Low', 'Low'),
    ('Medium', 'Medium'),
    ('High', 'High')]

LEVEL_OF_TRAINING_CHOICES = [
    ('Basic', 'Basic'),
    ('Intermediate', 'Intermediate'),
    ('Advanced', 'Advanced')]

YES_NO_CHOICES = (
    ('N', 'No'),
    ('Y', 'Yes')
)

YES_NO_MAYBE_CHOICES = (
    ('Yes', 'Yes'),
    ('No', 'No'),
    ('Possibly', 'Possibly')
)


class StatisticalMethodManager(models.Manager):
    '''Extends the Manager class to provide a query set that returns a data which has a method category of "STATISTICAL"
    '''

    def get_queryset(self):
        return super(StatisticalMethodManager, self).get_queryset().filter(method_subcategory__method_category__exact='STATISTICAL')


class WqsaCategoryMap(models.Model):
    wqsa_category_cd = models.IntegerField(primary_key=True)
    wqsa_category = models.CharField(max_length=2000, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'wqsa_category_map'


class MethodAbstract(models.Model):
    # Meta fields
    insert_date = models.DateField(null=True, blank=True)
    insert_person_name = models.CharField(max_length=50, blank=True)
    last_update_date = models.DateField(null=True, blank=True)
    last_update_person_name = models.CharField(max_length=50, blank=True)
    approved = models.CharField(max_length=1, default='N', choices=YES_NO_CHOICES)
    approved_date = models.DateField(null=True, blank=True)

    # General fields
    source_method_identifier = models.CharField(
        verbose_name='method number/identifier', max_length=45, unique=True,
        help_text='The method number / identifier can be numerical (e.g., 375.4), numerical w/text (e.g., 4500-SO4 C) or all text (e.g., Simplate). NOTE: If your method number ends in a "0" (e.g., 300.0), please contact the NEMI manager (entries ending in "0" are automatically truncated in Excel, and must be fixed by the NEMI manager).\nWhatever the format, you must choose a unique method number for your method. Also, keep things specific; do not use "Not Applicable," "Color Method" or something of that nature. If your method does not have a unique identifier, you must create one -- consider using a document number (e.g., EPA-XX-X-XXXX), product number, etc..\nIF a method has a published method number THEN include it ELSE create one',)
    method_descriptive_name = models.CharField(
        max_length=450, blank=True,
        help_text='This field is designed to provide the user with a quick identification of a method, so include the analyte (ex: "nitrate") or group of analytes (ex; "nutrients"), the matrix (ex: "in water"), and instrumentation (ex: "using colorimetry"):\nEx. 1: Nitrate in Water by Colorimetry\nEx. 2: Anions in Water by CIE-UV\nNOTE: If the general method includes multiple procedures for different analytes, create a Method entry for each subpart.',)
    method_type = models.ForeignKey(MethodTypeRef, models.CASCADE)
    method_subcategory = models.ForeignKey(
        MethodSubcategoryRef, models.CASCADE,
        null=True, blank=True,
        help_text='The "Method subcategory" describes the class of analytes that are measured by the method. Choose the appropriate subcategory (e.g., INORGANIC, RADIOCHEMICAL, MICROBIOLOGICAL) from the list of values. If your method does not fit into the available subcategories, or if you have a question about the meaning of the subcategories, contact the NEMI manager.')
    method_source = models.ForeignKey(
        MethodSourceRef, models.CASCADE,
        null=True, blank=True,
        help_text='The "Method source" is the organization that publishes a method.\nIF a method has a publication source THEN include it ELSE do not include method in database')
    source_citation = models.ForeignKey(
        SourceCitationRef, models.CASCADE, help_text='The "Source citation" is a reference to the publication/volume that contains the method. Choose the appropriate source citation (e.g., ASTM_11_01 - ASTM Vol. 11.01, MCAWW - Methods of Chemical Analysis for Water and Waste) from the list of values.\nIf your method does not fit into the available citations, contact the NEMI manager at jsulliv@usgs.gov.\nNOTE: Source citation acroynms are not always obvious -- always consult the Source citation list prior to selection one.')
    brief_method_summary = models.CharField(
        max_length=4000,
        help_text='Develop the "Brief method summary" using the Method Summary Section of the method. For example:\nSample, blanks and standards in sealed tubes are heated in an oven or block digestor in the presence of dichromate at 150 C. After two hours, the tubes are removed from the oven or digestor, cooled and measured spectrophotometrically at 600 nm.\nSome details in the summary are fine, but do not make it overly technical. The objective of the summary is to give the NEMI user an idea of how the method works and what it will take to run it, not how to run it.')
    media_name = models.ForeignKey(
        MediaNameDOM, models.CASCADE,
        null=True, blank=True, db_column='media_name',
        help_text='The "Media" describes the basic form of the sample that is analyze (not the specific matrix-type such as drinking or ground water). Choose the appropriate media (e.g., AIR, WATER) from the list of values.\nSpecific information (e.g., the method is used for "drinking water and groundwater" analyses) should be provided in the "Scope and Application" section.')
    method_official_name = models.CharField(
        max_length=250,
        help_text='This is the main heading of the method. For example for D2036: Standard Test Methods for Total Cyanides in Water After Distillation')
    instrumentation = models.ForeignKey(
        InstrumentationRef, models.CASCADE,
        help_text='The "Instrument" describes the instrumention used in the method. Choose the appropriate instrumentation from the list of values.\nNOTE: Only one value can be chosen for each method. If your method contains performance information for 2 or more instruments (e.g., GC-ECD and GC-MS), you make separate methods for each instrument, noting the instrument using "( )" after the method number (e.g. 502.2 (GC-PID) and 502.2 (GC-ELCD)).')
    waterbody_type = models.ForeignKey(
        WaterbodyTypeRef, models.CASCADE,
        null=True, db_column='waterbody_type',
        blank=True)
    scope_and_application = models.CharField(
        max_length=2000, blank=True,
        help_text='The "Scope and Application" field describes the (a) what is measured, and (b) under which conditions (e.g., matrices) the method can be used. For example:\nThis method covers the determination of acid semi-volatile compounds in surface waters, domestic and industrial wastes.')
    dl_type = models.ForeignKey(
        DlRef, models.CASCADE,
        null=True, blank=True, verbose_name='detection limit type',
        help_text='The "Detection limit type" describes the kind of detection (or quantitation) limit information that is found in the method (e.g., MDL, LOQ).\nNote: If separate detection and quantitation limits are provided, use detection limits.')
    dl_note = models.CharField(
        max_length=2000, blank=True, verbose_name='DL note',
        help_text='The "DL note" describes the conditions under which the detection (or quantitation) limits were determined. For example, were the detection limits determined in reagent water? What conditions were used? How many samples were run? Is their a detailed reference to the detection limit study that was performed? Examples:\nThe EDLs are estimated 3-sigma instrumental detection limits that were described in "EPA Method Study 27, Method 200.7 Trace Metals by ICP" [November 1983] (Available from National Technical Information Service as PB 85-248-656).\n(1) The values given are the minimum level at which the entire GC/MS system must give recognizable mass spectra (background corrected) and acceptable calibration points. (2) The values given refer to one of three techniques for each compound: internal standard quantification, labeled compound quantification, and isotope dilution quantification. Consult Table 3 of the method for information on specific compounds.\nMDLs were determined using the standard deviation of replicate analyses of an analyte-fortified reagent water sample multiplied by the t-value for (# of samples - 1) degrees of freedom atthe 99% confidence level. Detailed instructions for how MDLs are determined are found at 40 CFR part 136, Appendix B.')
    applicable_conc_range = models.CharField(
        max_length=300, blank=True,
        help_text='The "Applicable concentration range" field describes the effective range of the method (e.g., 0.02 - 1mg/L, > 0.037 Bq/L). Remember to (a) include units, and (b) include a range (e.g., if a radiochem method - with a detection limit (DL) but no effective upper end of the range - the range should be " > DL").\nNOTE: For multi-analyte methods, give a general range of applicability, noting an large deviations (e.g., all analytes are measured in the ug/L range except two, note the two in the different range).')
    conc_range_units = models.ForeignKey(
        DlUnitsDom, models.CASCADE,
        null=True, db_column='conc_range_units', blank=True,
        verbose_name='applicable concentration range')
    interferences = models.CharField(
        max_length=3000, blank=True,
        help_text='This field presents the potential interferences, along with remedies. For example:\n(A) Glassware contamination: Thoroughly clean glassware, including baking or solvent rinse.\n(B) Reagent contamination: Use high purity reagents.\n(C) Contamination from sample carryover: Rinsing apparatus with hexane and purging equipment between analyses can minimize contamination.\n(D) Extracted interferences: Interference from extracted non-target compounds, with retention times similar to target compounds, can be reduced by cleaning the extract or using confirmation analysis.\n(E) Variable solvents: Use the same solvent for each analysis.\n(F) Endrin degradation: The splitless injector may cause endrin degradation. Endrin can break down by reacting with the active sites on the port sleeve.\n(G) PCBs loss to glass surfaces: Rinse glass and minimize sample contact with glass to prevent adsorption loss of PCBs.\n(H) Oxidation of target compounds: Oxidation of compounds (specifically easily-oxidized aldrin, hexachlorocyclopentadiene, and methoxychlor) can be prevented by adding sodium thiosulfate at collection.\n(I) Phthalate interference: An unknown interference (possibly dibutyl phthalate) appears in heptachlors retention window.')
    precision_descriptor_notes = models.CharField(
        max_length=3000, blank=True,
        help_text='The "Precision Descriptor Notes" describe how precision and accuracy data were determined (including references to the number of labs used, types of matrices, number of samples, citation to report, etc.). For example:\nSummarized data results are based on quantification by isotope dilution. Precision and accuracy data was obtained from "Interlaboratory Validation of U.S. Environmental Protection Agency Method 1625A" (July 1984). Study data was collected for samples analyzed at 11-13 laboratories, depending on compounds. Approximately twenty-three percent of laboratories could not quantify or detect compounds by isotope dilution, so these laboratories were excluded from method summaries (the need for these exclusions was primarily based on lack of experience with the method at the time of the 1984 study).\nNote: See Analyte Entry Form for information on how to select precision and accuracy data from the method.\nIF a method contains precision descriptor notes that vary by analyte, provide a general summary of the notes here that is applicable to all analytes in the method. If necessary, direct users to the full method for additional analyte-specific information.')
    qc_requirements = models.CharField(
        max_length=2000, blank=True, verbose_name='QC requirements')
    sample_handling = models.CharField(max_length=3000, blank=True)
    max_holding_time = models.CharField(max_length=300, blank=True)
    sample_prep_methods = models.CharField(max_length=100, blank=True)
    relative_cost = models.ForeignKey(RelativeCostRef, models.CASCADE, null=True, blank=True)
    link_to_full_method = models.URLField(
        max_length=240, blank=True,
        verbose_name='Private Vendor URL (Do not enter URL for public methods)')
    regs_only = models.CharField(
        max_length=1, default='N', choices=YES_NO_CHOICES,
        verbose_name='regulation only method?',
        help_text='If you are reviewing this method, select your username from the list.')
    reviewer_name = models.CharField(
        max_length=100, blank=True,
        verbose_name='If you are reviewing this method, select your username from the list.')

    # CBR-only field
    rapidity = models.CharField(max_length=30, blank=True)
    screening = models.CharField(
        max_length=8, blank=True, choices=YES_NO_MAYBE_CHOICES)
    cbr_only = models.CharField(
        max_length=1, default='N', choices=YES_NO_CHOICES, verbose_name='CBR only?')

    # Greenness profile fields
    collected_sample_amt_ml = models.CharField(
        max_length=10, blank=True, verbose_name='collected sample amount (mL)')
    collected_sample_amt_g = models.CharField(
        max_length=10, blank=True, verbose_name='collected sample amount (g)')
    liquid_sample_flag = models.CharField(max_length=1, blank=True, null=True, choices=YES_NO_CHOICES)
    analysis_amt_ml = models.CharField(
        max_length=10, blank=True, verbose_name='analysis amount mL',
        help_text='The quantity of sample material that is selected to be treated and prepared for instrumental analysis. It is not the quantity of sample material that is left after sample treatment/preparation.')
    analysis_amt_g = models.CharField(
        max_length=10, blank=True, verbose_name='analysis amount G',
        help_text='The quantity of sample material that is selected to be treated and prepared for instrumental analysis. It is not the quantity of sample material that is left after sample treatment/preparation. If the analytical sample amount is given in mL, this is converted to grams, with the assumed density of 1 for water-based samples.')
    ph_of_analytical_sample = models.CharField(
        max_length=10, blank=True, verbose_name='pH of analytical sample',
        help_text='The pH of the sample when analyzed.')
    calc_waste_amt = models.DecimalField(
        null=True, max_digits=7, decimal_places=2, blank=True,
        verbose_name='calculated waste amount (g)',
        help_text='The sum of the amounts (in g) of the analytical sample and all chemicals used to treat the analytical sample.')
    quality_review_id = models.CharField(
        max_length=100, blank=True, verbose_name='QA reviewer ID')
    pbt = models.CharField(
        max_length=1, blank=True, choices=YES_NO_CHOICES,
        verbose_name='Does this method use a chemical considered to be PBT?',
        help_text='PBT: A chemical used in the method is listed as "persistent, bioaccumulative, and toxic (PBT)", as defined by the EPA\'s Toxic Release Inventory. \nEmergency Planning and Community Right-to-Know Act; Section 313; Toxic Release Inventory (TRI), the most recent chemical list available in 2006 is for the reporting year 2004, (available on the internet at http://www.epa.gov/tri/chemical/). If this method uses a chemical considered to be PBT by the above definition, select \'Y\'.')
    toxic = models.CharField(
        max_length=1, blank=True, choices=YES_NO_CHOICES,
        verbose_name="Does the method use a chemical listed on EPA's\nToxic Release Inventory (TRI) or RCRA's D, F, P, or U lists?",
        help_text="If the method uses a chemical listed on EPA's Toxic Release Inventory (TRI) or RCRA's D, F, P, or U lists it fails the greenness test for toxics, so the user should select 'Y'.")
    corrosive = models.CharField(
        max_length=1, blank=True, choices=YES_NO_CHOICES,
        verbose_name='Is the final pH of the sample less than 2 or greater than 12 (Corrosive)?',
        help_text="If the pH is less than 2 or greater than 12 the method fails the greenness test for corrosivity, so the user should select 'Y'.")
    waste = models.CharField(
        max_length=1, blank=True, choices=YES_NO_CHOICES,
        verbose_name='Is the waste from the method is greater than 50 grams?',
        help_text="If the waste from the method is greater than 50 grams, it fails the greenness test for waste, and the user should select 'Y'.")
    assumptions_comments = models.CharField(
        max_length=2000, blank=True, verbose_name='assumptions/comments')

    # Bio-assessment fields
    index_period = models.CharField(
        verbose_name='Index period',
        blank=True, null=True,
        max_length=240,
        help_text='If the method defines a sampling period, put that information here. Ex: "July 15 - Sept. 15"'
    )
    field_or_lab = models.CharField(
        blank=True, null=True,
        max_length=5,
        choices=((None, 'N/A'), ('Field', 'Field'), ('Lab', 'Lab')),
        verbose_name='Field or Lab',
        help_text='If the method defines field or lab processing ("pick") of invert samples or field or lab ID of fish species, use this field.'
    )
    mesh_size = models.CharField(
        blank=True, null=True,
        max_length=50,
        verbose_name='Mesh size',
        help_text='Can apply to invert nets as well as fish dipnets. If the method defines a mesh size, list it here. Include units. Ex: "595 um"'
    )
    sampling_reach_length = models.CharField(
        blank=True, null=True,
        max_length=240,
        verbose_name='Sampling reach length',
        help_text='Ex: "minimum 100 m"; "20x channel width (may be extended to capture two riffle-run or glide-pool sequences)"'
    )
    habitats_sampled = models.CharField(
        blank=True, null=True,
        max_length=240,
        verbose_name='Habitat(s) sampled',
        help_text='Ex: "riffle. in absence of riffle, sample overhanging veg. or in-stream snags"'
    )
    num_subsamples_composited = models.CharField(
        blank=True, null=True,
        max_length=50,
        verbose_name='Number of individual subsamples composited'
    )
    target_num_organisms = models.CharField(
        blank=True, null=True,
        max_length=240,
        verbose_name='Target number of organisms',
        help_text='Ex: "At least 200; extend sampling past 60 min to achieve if necessary"'
    )
    total_sampling_area = models.CharField(
        blank=True, null=True,
        max_length=240,
        verbose_name='Total sampling area',
        help_text='Ex: "All targeted habitats within reach"'
    )
    field_preservative = models.CharField(
        blank=True, null=True,
        max_length=16,
        verbose_name='Field preservative',
        choices=(
            (None, 'N/A'),
            ('Yes', 'Yes'),
            ('No', 'No'),
            ('Not Specified', 'Not Specified')
        )
    )
    taxa_included = models.CharField(
        blank=True, null=True,
        max_length=240,
        verbose_name='Taxa included'
    )
    laboratory_subsample = models.CharField(
        blank=True, null=True,
        max_length=240,
        verbose_name='Laboratory subsample?',
        help_text='Ex: "Yes"; "200 or 300 organisms +/- 20%"'
    )
    large_rare_pick = models.CharField(
        blank=True, null=True,
        verbose_name='Large/rare pick?',
        max_length=16,
        choices=(
            (None, 'N/A'),
            ('Yes', 'Yes'),
            ('No', 'No'),
            ('Not Specified', 'Not Specified')
        ),
        help_text='Choices: Yes. No. Not specified. N/A.'
    )

    # These fields are in the database, but not expose in the admin interface.
    matrix = models.CharField(max_length=12, blank=True, choices=(
        ('Freshwater', 'Freshwater'),
        ('Saltwater', 'Saltwater'),
        ('Both', 'Both'),
    ))
    technique = models.CharField(max_length=50, blank=True, choices=(
        ('Test Procedure', 'Test Procedure'),
        ('Sampling Procedure', 'Sampling Procedure'),
    ))
    etv_link = models.CharField(max_length=120,
                                blank=True)
    sam_complexity = models.CharField(max_length=10,
                                      blank=True,
                                      choices=COMPLEXITY_CHOICES)
    level_of_training = models.CharField(max_length=20,
                                         blank=True,
                                         choices=LEVEL_OF_TRAINING_CHOICES)
    media_emphasized_note = models.CharField(max_length=50,
                                             blank=True)
    media_subcategory = models.CharField(max_length=150,
                                         blank=True)
    notes = models.CharField(max_length=4000, blank=True)
    #wqsa_category_cd = models.ForeignKey(WqsaCategoryMap, db_column='wqsa_category_cd', blank=True, null=True)
    #owner_editable = models.CharField(max_length=1, blank=True, null=True, choices=YES_NO_CHOICES)

    objects = models.Manager()
    stat_methods = StatisticalMethodManager() # Use this manager to retrieve SAMS methods only

    class Meta:
        abstract = True

    def __str__(self):
        return self.source_method_identifier

    def get_insert_user(self):
        ''' Returns the User object for the person who inserted the object. If the user can not be found 'None' is returned.
        '''
        user_qs = User.objects.filter(username=self.insert_person_name)
        if user_qs:
            return user_qs[0]

        return User(username='Unknown')


COMMENTS_HELP_TEXT = 'This field is only to be used to communicate method entry status to the NEMI data review team, for example, if you will be entering 10 methods, you can report that in this field, "Method 1 of 10", "Method 2 of 10", etc. It would be particularly helpful to notify the team when you have entered the last of your batch of methods using this field so that they know to start reviewing the methods.'

class MethodOnline(MethodAbstract):

    method_id = models.AutoField(primary_key=True)
    no_analyte_flag = models.CharField(
        verbose_name='no analytes', max_length=4, blank=True, null=True,
        choices=YES_NO_CHOICES,
        help_text='Select if this method will not have analytes associated with it.',)
    comments = models.CharField(
        max_length=2000, blank=True, help_text=COMMENTS_HELP_TEXT)
    ready_for_review = models.CharField(max_length=1,
                                        choices=YES_NO_CHOICES,
                                        default='N')
    insert_person_name2 = models.CharField(max_length=100,
                                           blank=True) # Don't use this field for SAMS methods
    delete_after_load = models.CharField(max_length=1,
                                         choices=YES_NO_CHOICES,
                                         default='Y')

    class Meta:
        db_table = 'method_online'
        managed = True
        verbose_name = '#1 pending method'


class MethodStg(MethodAbstract):

    method_id = models.AutoField(primary_key=True)
    no_analyte_flag = models.CharField(
        verbose_name='no analytes', max_length=4, blank=True, null=True,
        choices=YES_NO_CHOICES,
        help_text='Select if this method will not have analytes associated with it.',)
    comments = models.CharField(
        max_length=2000, blank=True, help_text=COMMENTS_HELP_TEXT)
    ready_for_review = models.CharField(max_length=1,
                                        default='N',
                                        choices=YES_NO_CHOICES)
    date_loaded = models.DateField()

    class Meta:
        db_table = 'method_stg'
        managed = True
        verbose_name = '#2 in-review method'


class Method(MethodAbstract):

    method_id = models.IntegerField(primary_key=True)
    date_loaded = models.DateField(auto_now_add=True)

    class Meta:
        db_table = 'method'
        managed = True
        verbose_name = '#3 published method'


class StatisticalAnalysisType(models.Model):

    stat_analysis_index = models.IntegerField(primary_key=True)
    analysis_type = models.CharField(max_length=100)

    class Meta:
        db_table = 'statistical_analysis_type'
        ordering = ['analysis_type']
        managed = False

    def __str__(self):
        return self.analysis_type


class StatisticalDesignObjective(models.Model):

    stat_design_index = models.IntegerField(primary_key=True)
    objective = models.CharField(max_length=200)

    class Meta:
        db_table = 'statistical_design_objective'
        ordering = ['objective']
        managed = False

    def __str__(self):
        return self.objective


class StatisticalTopics(models.Model):

    stat_topic_index = models.IntegerField(primary_key=True)
    stat_special_topic = models.CharField(max_length=200)

    class Meta:
        db_table = 'statistical_topics'
        ordering = ['stat_special_topic']
        managed = False

    def __str__(self):
        return self.stat_special_topic


class StatAnalysisRelAbstract(models.Model):

    analysis_type = models.ForeignKey(
        StatisticalAnalysisType,
        models.DO_NOTHING,
        db_column='statisticalanalysistype_id'
    )

    class Meta:
        abstract = True

    def __str__(self):
        return str(self.analysis_type)


class StatAnalysisRelStg(StatAnalysisRelAbstract):

    method_id = models.IntegerField()

    class Meta:
        db_table = 'stat_analysis_rel_stg'
        ordering = ['analysis_type']
        managed = False


class StatAnalysisRel(StatAnalysisRelAbstract):

    method = models.ForeignKey(Method, models.CASCADE)

    class Meta:
        db_table = 'stat_analysis_rel'
        ordering = ['analysis_type']
        managed = False


class StatDesignRelAbstract(models.Model):

    design_objective = models.ForeignKey(
        StatisticalDesignObjective,
        models.DO_NOTHING,
        db_column='statisticaldesignobjective_id'
    )

    class Meta:
        abstract = True

    def __str__(self):
        return str(self.design_objective)


class StatDesignRelStg(StatDesignRelAbstract):

    method_id = models.IntegerField()

    class Meta:
        db_table = 'stat_design_rel_stg'
        ordering = ['design_objective']
        managed = False


class StatDesignRel(StatDesignRelAbstract):

    method = models.ForeignKey(Method, models.CASCADE)

    class Meta:
        db_table = 'stat_design_rel'
        ordering = ['design_objective']
        managed = False


class StatTopicRelAbstract(models.Model):

    topic = models.ForeignKey(StatisticalTopics, models.CASCADE, db_column='statisticaltopics_id')

    class Meta:
        abstract = True

    def __str__(self):
        return str(self.topic)


class StatTopicRelStg(StatTopicRelAbstract):

    method_id = models.IntegerField()

    class Meta:
        db_table = 'stat_topic_rel_stg'
        ordering = ['topic']
        managed = False


class StatTopicRel(StatTopicRelAbstract):

    method = models.ForeignKey(Method, models.CASCADE)

    class Meta:
        db_table = 'stat_topic_rel'
        ordering = ['topic']
        managed = False


class StatMediaRelAbstract(models.Model):

    media_name = models.ForeignKey(MediaNameDOM, models.CASCADE, db_column='medianamedom_id')

    class Meta:
        abstract = True

    def __str__(self):
        return str(self.media_name)


class StatMediaRelStg(StatMediaRelAbstract):

    method_id = models.IntegerField()

    class Meta:
        db_table = 'stat_media_rel_stg'
        ordering = ['media_name']
        managed = False


class StatMediaRel(StatMediaRelAbstract):

    method = models.ForeignKey(Method, models.CASCADE)

    class Meta:
        db_table = 'stat_media_rel'
        ordering = ['media_name']
        managed = False


class AnalyteSummaryVW(models.Model):
    dl_units = models.CharField(max_length=5, blank=True)
    dl_value = models.DecimalField(max_digits=15, decimal_places=6, null=True)
    accuracy = models.DecimalField(max_digits=15, decimal_places=6, null=True)
    accuracy_units = models.CharField(max_length=40, blank=True)
    precision = models.DecimalField(max_digits=15, decimal_places=6, null=True)
    precision_units = models.CharField(max_length=30, blank=True)
    prec_acc_conc_used = models.DecimalField(max_digits=15, decimal_places=6, null=True)
    false_positive_value = models.IntegerField(null=True)
    false_negative_value = models.IntegerField(null=True)
    analyte_code = models.CharField(max_length=20, blank=True)
    analyte_name = models.CharField(max_length=240, blank=True)
    dl_units_description = models.CharField(max_length=60, blank=True)
    precision_units_description = models.CharField(max_length=100, blank=True)
    accuracy_units_description = models.CharField(max_length=50, blank=True)
    precision_descriptor_notes = models.CharField(max_length=3000, blank=True)
    dl_note = models.CharField(max_length=2000, blank=True)
    preferred = models.IntegerField(blank=True)
    method_id = models.IntegerField(null=True)

    class Meta:
        db_table = 'analyte_summary_vw'
        managed = False


class MethodAnalyteVW(models.Model):

    sample_handling = models.CharField(max_length=3000, blank=True)
    max_holding_time = models.CharField(max_length=300, blank=True)
    sample_prep_methods = models.CharField(max_length=100, blank=True)
    relative_cost_id = models.IntegerField(null=True)
    method_source = models.CharField(max_length=20)
    method_source_name = models.CharField(max_length=150)
    method_source_url = models.CharField(max_length=200, blank=True)
    method_subcategory_id = models.IntegerField()
    method_category = models.CharField(max_length=50)
    method_subcategory = models.CharField(max_length=40)
    dl_type = models.CharField(max_length=11)
    dl_type_description = models.CharField(max_length=50)
    source_citation_name = models.CharField(max_length=450, blank=True)
    source_citation = models.CharField(max_length=30)
    source_citation_information = models.CharField(max_length=1500, blank=True)
    relative_cost_symbol = models.CharField(max_length=7, blank=True)
    relative_cost = models.CharField(max_length=40, blank=True)
    matrix = models.CharField(max_length=12, blank=True)
    dl_units = models.CharField(max_length=20)
    dl_value = models.DecimalField(max_digits=21, decimal_places=6, null=True)
    sub_dl_value = models.CharField(max_length=40, blank=True)
    analyte_method_id = models.IntegerField(primary_key=True)
    analyte_id = models.IntegerField()
    accuracy = models.DecimalField(max_digits=21, decimal_places=6, null=True)
    sub_accuracy = models.CharField(max_length=40, blank=True)
    accuracy_order = models.IntegerField(null=True)
    accuracy_units = models.CharField(max_length=40, blank=True)
    precision = models.DecimalField(max_digits=21, decimal_places=6, null=True)
    sub_precision = models.CharField(max_length=40, blank=True)
    precision_units = models.CharField(max_length=30, blank=True)
    prec_acc_conc_used = models.DecimalField(max_digits=21, decimal_places=6, null=True)
    false_positive_value = models.IntegerField(null=True)
    false_negative_value = models.IntegerField(null=True)
    analyte_code = models.CharField(max_length=20, blank=True)
    analyte_name = models.CharField(max_length=240, blank=True)
    preferred = models.IntegerField(null=True)
    analyte_cbr = models.CharField(max_length=1, blank=True)
    dl_units_description = models.CharField(max_length=60, blank=True)
    precision_units_description = models.CharField(max_length=100, blank=True)
    accuracy_units_description = models.CharField(max_length=50, blank=True)
    method_id = models.IntegerField(null=True)
    source_method_identifier = models.CharField(max_length=45)
    method_descriptive_name = models.CharField(max_length=250)
    method_official_name = models.CharField(max_length=250)
    method_source_id = models.IntegerField()
    source_citation_id = models.IntegerField()
    brief_method_summary = models.CharField(max_length=4000)
    scope_and_application = models.CharField(max_length=2000, blank=True)
    media_name = models.CharField(max_length=30)
    dl_type_id = models.IntegerField(null=True)
    dl_note = models.CharField(max_length=2000, blank=True)
    applicable_conc_range = models.CharField(max_length=300, blank=True)
    conc_range_units = models.CharField(max_length=20, blank=True)
    interferences = models.CharField(max_length=3000, blank=True)
    cbr_only = models.CharField(max_length=1, blank=True)
    qc_requirements = models.CharField(max_length=2000, blank=True)
    instrumentation_id = models.IntegerField()
    instrumentation = models.CharField(max_length=20)
    instrumentation_description = models.CharField(max_length=200)
    precision_descriptor_notes = models.CharField(max_length=3000, blank=True)
    link_to_full_method = models.CharField(max_length=240, blank=True)

    class Meta:
        managed = False
        db_table = 'method_analyte_vw'


class UserRole(models.Model):
    role_name = models.CharField(primary_key=True, max_length=400)
    role_description = models.CharField(max_length=400, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'user_roles'


class LegacyUserAccount(models.Model):
    """
    Legacy user account that was used for method submission.
    """
    user_seq = models.FloatField(primary_key=True)
    user_name = models.CharField(unique=True, max_length=100)
    user_password = models.TextField(blank=True, null=True)  # This field type is a guess.
    user_role = models.ForeignKey(UserRole, models.DO_NOTHING, db_column='user_role')
    email = models.CharField(unique=True, max_length=200)
    forgot_pw_flag = models.CharField(max_length=1)
    data_entry_name = models.CharField(max_length=100)
    data_entry_date = models.DateField()
    last_update_name = models.CharField(max_length=100, blank=True, null=True)
    last_update_date = models.DateField(blank=True, null=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=200)
    organization = models.CharField(max_length=1000, blank=True, null=True)
    last_login = models.DateField(blank=True, null=True)
    user_status = models.CharField(max_length=40)

    class Meta:
        managed = False
        db_table = 'user_account'


class RevisionManager(models.Manager):
    def get_queryset(self):
        queryset = super(RevisionManager, self).get_queryset()
        return queryset.defer('method_pdf')


class AbstractRevision(models.Model):
    objects = RevisionManager()

    revision_id = models.AutoField(primary_key=True)

    revision_flag = models.BooleanField(db_column='revision_flag')
    revision_information = models.CharField(max_length=100)

    insert_date = models.DateField(
        blank=True, null=True, auto_now_add=True, editable=False)
    insert_person_name = models.CharField(
        max_length=50, blank=True, null=True, editable=False)
    last_update_date = models.DateField(blank=True, null=True, auto_now=True)
    last_update_person_name = models.CharField(
        max_length=50, blank=True, null=True, editable=False)

    pdf_insert_person = models.CharField(max_length=20, blank=True, null=True)
    pdf_insert_date = models.DateField(blank=True, null=True)
    method_pdf = models.BinaryField(blank=True, null=True)
    mimetype = models.CharField(max_length=50, blank=True, null=True)

    class Meta:
        abstract = True

    def __str__(self):
        return self.revision_information


class RevisionJoin(AbstractRevision):
    method = models.ForeignKey(
        Method, models.CASCADE,
        blank=True, null=True, related_name='revisions')
    source_citation = models.ForeignKey(
        SourceCitationRef, models.SET_NULL, blank=True, null=True)
    date_loaded = models.DateField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'revision_join'
        unique_together = (('method', 'revision_information', 'source_citation'),)
        verbose_name = 'revision'


class RevisionJoinOnline(AbstractRevision):
    #method_id = models.IntegerField()
    method = models.ForeignKey(
        MethodOnline, models.SET_NULL,
        blank=True, null=True, related_name='revisions')
    source_citation = models.ForeignKey(
        SourceCitationOnlineRef, models.SET_NULL, blank=True, null=True)
    reviewer_name = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'revision_join_online'
        unique_together = (('method', 'revision_information'),)
        verbose_name = 'pending revision'


class RevisionJoinStg(AbstractRevision):
    method = models.ForeignKey(
        MethodStg, models.SET_NULL,
        blank=True, null=True, related_name='revisions')
    source_citation = models.ForeignKey(
        SourceCitationStgRef, models.SET_NULL, blank=True, null=True)
    date_loaded = models.DateField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'revision_join_stg'
        unique_together = (('method', 'revision_information', 'source_citation'),)
        verbose_name = 'staging revision'


class ProtocolSourceCitationStgRef(refs.SourceCitationStgRef):
    class Meta:
        managed = False
        proxy = True
        verbose_name = 'protocol source citation'


class ProtocolRevisionJoinStg(AbstractRevision):
    method = models.ForeignKey(
        MethodStg, models.SET_NULL,
        blank=True, null=True, related_name='protocol_revisions')
    source_citation = models.ForeignKey(
        ProtocolSourceCitationStgRef, models.SET_NULL,
        blank=True, null=True)
    date_loaded = models.DateField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'revision_join_stg'
        unique_together = (('method', 'revision_information', 'source_citation'),)
        verbose_name = 'staging revision'


class AbstractAnalyteMethodJn(models.Model):
    class Meta:
        abstract = True

    analyte_method_id = models.AutoField(primary_key=True)
    analyte = models.ForeignKey(refs.AnalyteRef, models.DO_NOTHING)
    dl_value = models.DecimalField(max_digits=15, decimal_places=6, blank=True, null=True)
    #dl_units = models.ForeignKey(refs.DlUnitsDom, models.DO_NOTHING, db_column='dl_units')
    dl_units = models.CharField(max_length=50, blank=True, null=True)
    accuracy = models.DecimalField(max_digits=15, decimal_places=6, blank=True, null=True)
    accuracy_units = models.ForeignKey(refs.AccuracyUnitsDom, models.DO_NOTHING, db_column='accuracy_units', blank=True, null=True)
    false_positive_value = models.IntegerField(blank=True, null=True)
    false_negative_value = models.IntegerField(blank=True, null=True)
    precision = models.DecimalField(max_digits=15, decimal_places=6, blank=True, null=True)
    precision_units = models.ForeignKey(refs.PrecisionUnitsDom, models.DO_NOTHING, db_column='precision_units', blank=True, null=True)
    prec_acc_conc_used = models.DecimalField(max_digits=15, decimal_places=6, blank=True, null=True)
    insert_date = models.DateField(blank=True, null=True)
    insert_person_name = models.CharField(max_length=50, blank=True, null=True)
    last_update_date = models.DateField(blank=True, null=True)
    last_update_person_name = models.CharField(max_length=50, blank=True, null=True)
    green_flag = models.CharField(max_length=1, blank=True, null=True)
    yellow_flag = models.CharField(max_length=1, blank=True, null=True)
    confirmatory = models.CharField(max_length=8, blank=True, null=True, choices=(
        ('Yes', 'Yes'),
        ('No', 'No'),
        ('Possibly', 'Possibly'),
        ('N/A', 'N/A'),
    ))

    def __str__(self):
        return str(self.analyte_method_id)


class AnalyteMethodJn(AbstractAnalyteMethodJn):
    method = models.ForeignKey(
        Method, models.CASCADE, related_name='analytes')
    date_loaded = models.DateField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'analyte_method_jn'
        unique_together = (('method', 'analyte'),)
        verbose_name = 'method analyte'


class AnalyteMethodJnOnline(AbstractAnalyteMethodJn):
    method = models.ForeignKey(
        MethodOnline, models.CASCADE, related_name='analytes')
    reviewer_name = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'analyte_method_jn_online'
        unique_together = (('method', 'analyte'),)
        verbose_name = 'method analyte'


class AnalyteMethodJnStg(AbstractAnalyteMethodJn):
    method = models.ForeignKey(MethodStg, models.CASCADE, related_name='analytes')
    date_loaded = models.DateField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'analyte_method_jn_stg'
        unique_together = (('method', 'analyte'),)
        verbose_name = 'method analyte'


class AbstractProtocolMethodRel(models.Model):
    protocol_method_id = models.AutoField(primary_key=True)

    class Meta:
        abstract = True

    def __str__(self):
        return str(self.method)


class ProtocolMethodOnlineRel(AbstractProtocolMethodRel):
    source_citation = models.ForeignKey(
        SourceCitationOnlineRef, models.CASCADE, related_name='protocols')
    method = models.ForeignKey(
        MethodOnline, models.CASCADE, related_name='protocols')

    class Meta:
        managed = False
        db_table = 'protocol_method_online_rel'


class ProtocolMethodRel(AbstractProtocolMethodRel):
    source_citation = models.ForeignKey(
        SourceCitationRef, models.CASCADE, related_name='protocols')
    method = models.ForeignKey(
        Method, models.CASCADE, related_name='protocols')

    class Meta:
        managed = False
        db_table = 'protocol_method_rel'


class ProtocolMethodStgRel(AbstractProtocolMethodRel):
    source_citation = models.ForeignKey(
        ProtocolSourceCitationStgRef, models.CASCADE,
        related_name='protocols')
    method = models.ForeignKey(
        MethodStg, models.CASCADE, related_name='protocols')

    class Meta:
        managed = False
        db_table = 'protocol_method_stg_rel'
        verbose_name = 'protocol method'
