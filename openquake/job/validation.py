# Copyright (c) 2010-2013, GEM Foundation.
#
# OpenQuake is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# OpenQuake is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with OpenQuake.  If not, see <http://www.gnu.org/licenses/>.

"""
This module contains functions and Django model forms for carrying out job
profile validation.
"""


import re

from django.forms import ModelForm
import nhlib

from openquake.db import models

#: Minimum value for a signed 32-bit int
MIN_SINT_32 = -(2 ** 31)
#: Maximum value for a signed 32-bit int
MAX_SINT_32 = (2 ** 31) - 1

AVAILABLE_GSIMS = nhlib.gsim.get_available_gsims().keys()


class BaseOQModelForm(ModelForm):
    """
    This class is based on :class:`django.forms.ModelForm`. Constructor
    arguments are the same.

    Since we're using forms (at the moment) purely for model validation, it's
    worth noting how we're using forms and what sort of inputs should be
    supplied.

    At the very least, an `instance` should be specified, which is expected to
    be a Django model object (perhaps one from :mod:`openquake.db.models`).

    `data` can be specified to populate the form and model. If no `data` is
    specified, the form will take the current data from the `instance`.

    You can also specify `files`. In the Django web form context, this
    represents a `dict` of name-file_object pairs. The file object type can be,
    for example, one of the types in :mod:`django.core.files.uploadedfile`.

    In this case, however, we expect `files` to be a dict of
    :class:`openquake.db.models.Input`, keyed by config file parameter for the
    input. For example::

    {'site_model_file': <Input: 174||site_model||0xdeadbeef||>}
    """

    # These fields require more complex validation.
    # The rules for these fields depend on other parameters
    # and files.
    # At the moment, these are common to all hazard calculation modes.
    special_fields = (
        'export_dir',
    )

    def __init__(self, *args, **kwargs):
        self.exports = kwargs.get('exports')
        if not 'data' in kwargs:
            # Because we're not using ModelForms in exactly the
            # originally-intended modus operandi, we need to pass all of the
            # field values from the instance model object as the `data` kwarg
            # (`data` needs to be a dict of fieldname-value pairs).
            # This serves to populate the form (as if a user had done so) and
            # immediately enables validation checking (through `is_valid()`,
            # for example).
            # This is, of course, only applicable if `instance` was supplied to
            # the form. For the purpose of just doing validation (which is why
            # these forms were created), we need to specify the `instance`.
            instance = kwargs.get('instance')
            if instance is not None:
                kwargs['data'] = instance.__dict__
        if "exports" in kwargs:
            del kwargs['exports']
        super(BaseOQModelForm, self).__init__(*args, **kwargs)

    def _add_error(self, field_name, error_msg):
        """
        Add an error to the `errors` dict.

        If errors for the given ``field_name`` already exist append the error
        to that list. Otherwise, a new entry will have to be created for the
        ``field_name`` to hold the ``error_msg``.

        ``error_msg`` can also be a list or tuple of error messages.
        """
        is_list = isinstance(error_msg, (list, tuple))
        if self.errors.get(field_name) is not None:
            if is_list:
                self.errors[field_name].extend(error_msg)
            else:
                self.errors[field_name].append(error_msg)
        else:
            # no errors for this field have been recorded yet
            if is_list:
                if len(error_msg) > 0:
                    self.errors[field_name] = error_msg
            else:
                self.errors[field_name] = [error_msg]

    def is_valid(self):
        """
        Overrides :meth:`django.forms.ModelForm.is_valid` to perform
        custom validation checks (in addition to superclass validation).

        :returns:
            If valid return `True`, else `False`.
        """
        super_valid = super(BaseOQModelForm, self).is_valid()
        all_valid = super_valid

        # Calculation
        calc = self.instance

        # First, check the calculation mode:
        valid, errs = calculation_mode_is_valid(calc, self.calc_mode)
        all_valid &= valid
        self._add_error('calculation_mode', errs)

        # Exclude special fields that require contextual validation.
        fields = self.__class__.Meta.fields

        for field in sorted(set(fields) - set(self.special_fields)):
            valid, errs = globals()['%s_is_valid' % field](calc)
            all_valid &= valid

            self._add_error(field, errs)

        if self.exports:
            # The user has requested that exports be performed after the
            # calculation i.e. an 'export_dir' parameter must be present.
            if not calc.export_dir:
                all_valid = False
                err = ('--exports specified on the command line but the '
                       '"export_dir" parameter is missing in the .ini file')
                self._add_error('export_dir', err)

        return all_valid


class BaseHazardModelForm(BaseOQModelForm):
    """
    Base ModelForm used to validate HazardCalculation objects
    """

    special_fields = (
        'region',
        'region_grid_spacing',
        'sites',
        'reference_vs30_value',
        'reference_vs30_type',
        'reference_depth_to_2pt5km_per_sec',
        'reference_depth_to_1pt0km_per_sec',
        'export_dir',
    )

    def is_valid(self):
        super_valid = super(BaseHazardModelForm, self).is_valid()
        all_valid = super_valid

        # HazardCalculation
        hc = self.instance
        # Now do checks which require more context.

        # Cannot specify region AND sites
        if (hc.region is not None and hc.sites is not None):
            all_valid = False
            err = 'Cannot specify `region` and `sites`. Choose one.'
            self._add_error('region', err)
        # At least one must be specified (region OR sites)
        elif not (hc.region is not None or hc.sites is not None):
            all_valid = False
            err = 'Must specify either `region` or `sites`.'
            self._add_error('region', err)
            self._add_error('sites', err)
        # Only region is specified
        elif hc.region is not None:
            if hc.region_grid_spacing is not None:
                valid, errs = region_grid_spacing_is_valid(hc)
                all_valid &= valid

                self._add_error('region_grid_spacing', errs)
            else:
                all_valid = False
                err = '`region` requires `region_grid_spacing`'
                self._add_error('region', err)

            # validate the region
            valid, errs = region_is_valid(hc)
            all_valid &= valid
            self._add_error('region', errs)
        # Only sites was specified
        else:
            valid, errs = sites_is_valid(hc)
            all_valid &= valid
            self._add_error('sites', errs)

        if 'site_model_file' not in self.files:
            # make sure the reference parameters are defined and valid

            for field in (
                'reference_vs30_value',
                'reference_vs30_type',
                'reference_depth_to_2pt5km_per_sec',
                'reference_depth_to_1pt0km_per_sec',
            ):
                valid, errs = eval('%s_is_valid' % field)(hc)
                all_valid &= valid
                self._add_error(field, errs)

        return all_valid


class ClassicalHazardCalculationForm(BaseHazardModelForm):

    calc_mode = 'classical'

    class Meta:
        model = models.HazardCalculation
        fields = (
            'description',
            'no_progress_timeout',
            'region',
            'region_grid_spacing',
            'sites',
            'random_seed',
            'number_of_logic_tree_samples',
            'rupture_mesh_spacing',
            'width_of_mfd_bin',
            'area_source_discretization',
            'reference_vs30_value',
            'reference_vs30_type',
            'reference_depth_to_2pt5km_per_sec',
            'reference_depth_to_1pt0km_per_sec',
            'investigation_time',
            'intensity_measure_types_and_levels',
            'truncation_level',
            'maximum_distance',
            'mean_hazard_curves',
            'quantile_hazard_curves',
            'poes_hazard_maps',
            'export_dir',
        )


class EventBasedHazardCalculationForm(BaseHazardModelForm):

    calc_mode = 'event_based'

    class Meta:
        model = models.HazardCalculation
        fields = (
            'description',
            'no_progress_timeout',
            'region',
            'region_grid_spacing',
            'sites',
            'random_seed',
            'number_of_logic_tree_samples',
            'rupture_mesh_spacing',
            'width_of_mfd_bin',
            'area_source_discretization',
            'reference_vs30_value',
            'reference_vs30_type',
            'reference_depth_to_2pt5km_per_sec',
            'reference_depth_to_1pt0km_per_sec',
            'investigation_time',
            'truncation_level',
            'maximum_distance',
            'intensity_measure_types',
            'intensity_measure_types_and_levels',
            'ses_per_logic_tree_path',
            'ground_motion_correlation_model',
            'ground_motion_correlation_params',
            'complete_logic_tree_ses',
            'complete_logic_tree_gmf',
            'ground_motion_fields',
            'hazard_curves_from_gmfs',
            'mean_hazard_curves',
            'quantile_hazard_curves',
            'poes_hazard_maps',
            'export_dir',
        )

    def is_valid(self):
        super_valid = super(EventBasedHazardCalculationForm, self).is_valid()
        all_valid = super_valid

        hc = self.instance

        # contextual validation

        # It doesn't make sense to capture/export the `complete_logic_tree_gmf`
        # when we're doing end-branch enumeration:
        if not hc.number_of_logic_tree_samples and hc.complete_logic_tree_gmf:

            msg = '`%s` is not available with end branch enumeration'
            msg %= 'complete_logic_tree_gmf'
            self._add_error('complete_logic_tree_gmf', msg)
            all_valid = False

        # For the case where the user has requested to post-process GMFs into
        # hazard curves:
        if hc.hazard_curves_from_gmfs:
            # 1) We need to make sure `intensity_measure_types_and_levels` is
            #    defined (and valid)
            if hc.intensity_measure_types_and_levels is None:
                # Not defined
                msg = '`%s` requires `%s`'
                msg %= ('hazard_curve_from_gmfs',
                        'intensity_measure_types_and_levels')

                self._add_error('intensity_measure_types_and_levels', msg)
                all_valid = False
            else:
                # Defined, but is it valid?
                valid, errs = intensity_measure_types_and_levels_is_valid(hc)
                all_valid &= valid
                self._add_error('hazard_curves_from_gmfs', errs)

                # 2) The IMT keys in `intensity_measure_types_and_levels` need
                #    to be a subset of `intensity_measure_types`.
                imts = set(hc.intensity_measure_types_and_levels.keys())
                all_imts = set(hc.intensity_measure_types)

                if not imts.issubset(all_imts):
                    msg = 'Unknown IMT(s) [%s] in `%s`'
                    msg %= (', '.join(sorted(imts - all_imts)),
                            'intensity_measure_types')

                    self._add_error('intensity_measure_types_and_levels', msg)
                    all_valid = False

        return all_valid


class DisaggHazardCalculationForm(BaseHazardModelForm):

    calc_mode = 'disaggregation'

    class Meta:
        model = models.HazardCalculation
        fields = (
            'description',
            'no_progress_timeout',
            'region',
            'region_grid_spacing',
            'sites',
            'random_seed',
            'number_of_logic_tree_samples',
            'rupture_mesh_spacing',
            'width_of_mfd_bin',
            'area_source_discretization',
            'reference_vs30_value',
            'reference_vs30_type',
            'reference_depth_to_2pt5km_per_sec',
            'reference_depth_to_1pt0km_per_sec',
            'investigation_time',
            'intensity_measure_types_and_levels',
            'truncation_level',
            'maximum_distance',
            'mag_bin_width',
            'distance_bin_width',
            'coordinate_bin_width',
            'num_epsilon_bins',
            'poes_disagg',
            'export_dir',
        )


class ScenarioHazardCalculationForm(BaseHazardModelForm):

    calc_mode = 'scenario'

    class Meta:
        model = models.HazardCalculation
        fields = (
            'description',
            'region',
            'region_grid_spacing',
            'sites',
            'random_seed',
            'rupture_mesh_spacing',
            'reference_vs30_value',
            'reference_vs30_type',
            'reference_depth_to_2pt5km_per_sec',
            'reference_depth_to_1pt0km_per_sec',
            'intensity_measure_types',
            'truncation_level',
            'maximum_distance',
            'number_of_ground_motion_fields',
            'gsim',
            'export_dir',
        )

#: Maps calculation_mode to the appropriate validator class
HAZ_VALIDATOR_MAP = {
    'classical': ClassicalHazardCalculationForm,
    'event_based': EventBasedHazardCalculationForm,
    'disaggregation': DisaggHazardCalculationForm,
    'scenario': ScenarioHazardCalculationForm,
}


class ClassicalRiskCalculationForm(BaseOQModelForm):
    calc_mode = 'classical'

    class Meta:
        model = models.RiskCalculation
        fields = (
            'description',
            'no_progress_timeout',
            'region_constraint',
            'lrem_steps_per_interval',
            'conditional_loss_poes',
        )


class ClassicalRiskCalculationWithBCRForm(BaseOQModelForm):
    calc_mode = 'classical_bcr'

    class Meta:
        fields = (
            'description',
            'no_progress_timeout',
            'region_constraint',
            'lrem_steps_per_interval',
            'interest_rate',
            'asset_life_expectancy',
        )


class EventBasedRiskCalculationWithBCRForm(BaseOQModelForm):
    calc_mode = 'event_based_bcr'

    class Meta:
        fields = (
            'description',
            'no_progress_timeout',
            'region_constraint',
            'loss_curve_resolution',
            'master_seed',
            'asset_correlation',
            'interest_rate',
            'asset_life_expectancy',
        )


class EventBasedRiskCalculationForm(BaseOQModelForm):
    calc_mode = 'event_based'

    class Meta:
        fields = (
            'description',
            'no_progress_timeout',
            'region_constraint',
            'loss_curve_resolution',
            'insured_losses',
            'master_seed',
            'asset_correlation',
        )


class ScenarioDamageRiskCalculationForm(BaseOQModelForm):
    calc_mode = 'scenario_damage'

    class Meta:
        fields = (
            'description',
            'region_constraint',
        )

#: Maps calculation_mode to the appropriate validator class
RISK_VALIDATOR_MAP = {
    'classical': ClassicalRiskCalculationForm,
    'classical_bcr': ClassicalRiskCalculationWithBCRForm,
    'event_based': EventBasedRiskCalculationForm,
    'event_based_bcr': EventBasedRiskCalculationWithBCRForm,
    'scenario_damage': ScenarioDamageRiskCalculationForm,
}


# Silencing 'Missing docstring' and 'Invalid name' for all of the validation
# functions (the latter because some of the function names are very long).
# pylint: disable=C0111,C0103


def description_is_valid(_mdl):
    return True, []


def calculation_mode_is_valid(mdl, expected_calc_mode):
    if not mdl.calculation_mode == expected_calc_mode:
        return False, ['Calculation mode must be "%s"' % expected_calc_mode]
    return True, []


def region_is_valid(mdl):
    valid = True
    errors = []

    if not mdl.region.valid:
        valid = False
        errors.append('Invalid region geomerty: %s' % mdl.region.valid_reason)

    if len(mdl.region.coords) > 1:
        valid = False
        errors.append('Region geometry can only be a single linear ring')

    # There should only be a single linear ring.
    # Even if there are multiple, we can still check for and report errors.
    for ring in mdl.region.coords:
        lons = [lon for lon, _ in ring]
        lats = [lat for _, lat in ring]
        if not all([-180 <= x <= 180 for x in lons]):
            valid = False
            errors.append('Longitude values must in the range [-180, 180]')
        if not all([-90 <= x <= 90 for x in lats]):
            valid = False
            errors.append('Latitude values must be in the range [-90, 90]')
    return valid, errors


def region_grid_spacing_is_valid(mdl):
    if not mdl.region_grid_spacing > 0:
        return False, ['Region grid spacing must be > 0']
    return True, []


def no_progress_timeout_is_valid(mdl):
    if not mdl.no_progress_timeout > 0:
        return False, ['"No progress" time-out must be > 0']
    return True, []


def sites_is_valid(mdl):
    valid = True
    errors = []

    lons = [pt.x for pt in mdl.sites]
    lats = [pt.y for pt in mdl.sites]
    if not all([-180 <= x <= 180 for x in lons]):
        valid = False
        errors.append('Longitude values must in the range [-180, 180]')
    if not all([-90 <= x <= 90 for x in lats]):
        valid = False
        errors.append('Latitude values must be in the range [-90, 90]')

    return valid, errors


def random_seed_is_valid(mdl):
    if not MIN_SINT_32 <= mdl.random_seed <= MAX_SINT_32:
        return False, [('Random seed must be a value from %s to %s (inclusive)'
                       % (MIN_SINT_32, MAX_SINT_32))]
    return True, []


def number_of_logic_tree_samples_is_valid(mdl):
    if not mdl.number_of_logic_tree_samples >= 0:
        return False, ['Number of logic tree samples must be >= 0']
    return True, []


def rupture_mesh_spacing_is_valid(mdl):
    if not mdl.rupture_mesh_spacing > 0:
        return False, ['Rupture mesh spacing must be > 0']
    return True, []


def width_of_mfd_bin_is_valid(mdl):
    if not mdl.width_of_mfd_bin > 0:
        return False, ['Width of MFD bin must be > 0']
    return True, []


def area_source_discretization_is_valid(mdl):
    if not mdl.area_source_discretization > 0:
        return False, ['Area source discretization must be > 0']
    return True, []


def reference_vs30_value_is_valid(mdl):
    if not mdl.reference_vs30_value > 0:
        return False, ['Reference VS30 value must be > 0']
    return True, []


def reference_vs30_type_is_valid(mdl):
    if not mdl.reference_vs30_type in ('measured', 'inferred'):
        return False, ['Reference VS30 type must be either '
                       '"measured" or "inferred"']
    return True, []


def reference_depth_to_2pt5km_per_sec_is_valid(mdl):
    if not mdl.reference_depth_to_2pt5km_per_sec > 0:
        return False, ['Reference depth to 2.5 km/sec must be > 0']
    return True, []


def reference_depth_to_1pt0km_per_sec_is_valid(mdl):
    if not mdl.reference_depth_to_1pt0km_per_sec > 0:
        return False, ['Reference depth to 1.0 km/sec must be > 0']
    return True, []


def investigation_time_is_valid(mdl):
    if not mdl.investigation_time > 0:
        return False, ['Investigation time must be > 0']
    return True, []


def _validate_imt(imt):
    """
    Validate an intensity measure type string.

    :returns:
        A pair of values. The first is a `bool` indicating whether or not the
        IMT is valid. The second value is a `list` of error messages. (If the
        IMT is valid, the list should be empty.)
    """
    valid = True
    errors = []

    # SA intensity measure configs need special handling
    valid_imts = list(set(nhlib.imt.__all__) - set(['SA']))

    if 'SA' in imt:
        match = re.match(r'^SA\(([^)]+?)\)$', imt)
        if match is None:
            # SA key is not formatted properly
            valid = False
            errors.append(
                '%s: SA must be specified with a period value, in the form'
                ' `SA(N)`, where N is a value >= 0' % imt
            )
        else:
            # there's a match; make sure the period value is valid
            sa_period = match.groups()[0]
            try:
                if float(sa_period) < 0:
                    valid = False
                    errors.append(
                        '%s: SA period values must be >= 0' % imt
                    )
            except ValueError:
                valid = False
                errors.append(
                    '%s: SA period value should be a float >= 0' % imt
                )
    elif not imt in valid_imts:
        valid = False
        errors.append('%s: Invalid intensity measure type' % imt)

    return valid, errors


def intensity_measure_types_and_levels_is_valid(mdl):
    im = mdl.intensity_measure_types_and_levels

    valid = True
    errors = []

    if mdl.calculation_mode == 'event_based' and im is None:
        # For event-based hazard calculations, this parameter is optional
        return valid, errors

    for im_type, imls in im.iteritems():
        # validate IMT:
        valid_imt, imt_errors = _validate_imt(im_type)
        valid &= valid_imt
        errors.extend(imt_errors)

        # validate IML values:
        if not isinstance(imls, list):
            valid = False
            errors.append(
                '%s: IMLs must be specified as a list of floats' % im_type
            )
        else:
            if len(imls) == 0:
                valid = False
                errors.append(
                    '%s: IML lists must have at least 1 value' % im_type
                )
            elif not all([x > 0 for x in imls]):
                valid = False
                errors.append('%s: IMLs must be > 0' % im_type)

    return valid, errors


def intensity_measure_types_is_valid(mdl):
    imts = mdl.intensity_measure_types

    valid = True
    errors = []

    for imt in imts:
        valid_imt, imt_errors = _validate_imt(imt)
        valid &= valid_imt
        errors.extend(imt_errors)

    return valid, errors


# FIXME
# This function and similar ones where different
# checking rules are applied according to
# different calculation modes need to be refactored,
# splitting up the checking rules for each calculation
# mode.
def truncation_level_is_valid(mdl):
    if mdl.calculation_mode == 'disaggregation':
        if mdl.truncation_level is not None:
            if mdl.truncation_level <= 0:
                return False, [
                    'Truncation level must be > 0 for disaggregation'
                    ' calculations']
        else:
            return False, [
                'Truncation level must be set for disaggregation'
                ' calculations and it must be > 0']
    else:
        if mdl.truncation_level is not None:
            if mdl.truncation_level < 0:
                return False, ['Truncation level must be >= 0']

    return True, []


def maximum_distance_is_valid(mdl):
    if not mdl.maximum_distance > 0:
        return False, ['Maximum distance must be > 0']
    return True, []


def mean_hazard_curves_is_valid(_mdl):
    # The validation form should normalize the type to a boolean.
    # We don't need to check anything here.
    return True, []


def quantile_hazard_curves_is_valid(mdl):
    qhc = mdl.quantile_hazard_curves

    if qhc is not None:
        if not all([0.0 <= x <= 1.0 for x in qhc]):
            return False, ['Quantile hazard curve values must in the range '
                           '[0, 1]']
    return True, []


def poes_hazard_maps_is_valid(mdl):
    phm = mdl.poes_hazard_maps
    error_msg = 'PoEs for hazard maps must be in the range [0, 1]'
    return _validate_poe_list(phm, error_msg)


def _validate_poe_list(poes, error_msg):
    if poes is not None:
        if not all([0.0 <= x <= 1.0 for x in poes]):
            return False, [error_msg]
    return True, []


def ses_per_logic_tree_path_is_valid(mdl):
    sps = mdl.ses_per_logic_tree_path

    if not sps > 0:
        return False, ['`Stochastic Event Sets Per Sample` '
                       '(ses_per_logic_tree_path) must be > 0']
    return True, []


def ground_motion_correlation_model_is_valid(_mdl):
    # No additional validation is required;
    # the model form and fields will take care of validation based on the
    # valid choices defined for this field.
    return True, []


def ground_motion_correlation_params_is_valid(_mdl):
    # No additional validation is required;
    # it is not appropriate to do detailed checks on the correlation model
    # parameters at this point because the parameters are specific to a given
    # correlation model.
    # Field normalization should make sure that the input is properly formed.
    return True, []


def complete_logic_tree_ses_is_valid(_mdl):
    # This parameter is a simple True or False;
    # field normalization should cover all of validation necessary.
    return True, []


def complete_logic_tree_gmf_is_valid(_mdl):
    # This parameter is a simple True or False;
    # field normalization should cover all of validation necessary.
    return True, []


def ground_motion_fields_is_valid(_mdl):
    # This parameter is a simple True or False;
    # field normalization should cover all of validation necessary.
    return True, []


def hazard_curves_from_gmfs_is_valid(_mdl):
    # This parameter is a simple True or False;
    # field normalization should cover all of validation necessary.
    return True, []


def conditional_loss_poes_is_valid(mdl):
    value = mdl.conditional_loss_poes

    if value is not None:
        if not all([0.0 <= x <= 1.0 for x in value]):
            return (
                False,
                ['PoEs for conditional loss poes must be in the range [0, 1]'])
    return True, []


def lrem_steps_per_interval_is_valid(mdl):
    value = mdl.lrem_steps_per_interval
    msg = 'loss conditional exceedence matrix steps per interval must be > 0'

    if value is None or not value > 0:
        return False, [msg]
    return True, []


def region_constraint_is_valid(_mdl):
    # At this stage, we just use the region_is_valid implementation to
    # check for a consistent geometry. Further validation occurs after
    # we have loaded the exposure.
    _mdl.region = _mdl.region_constraint
    return region_is_valid(_mdl)


def mag_bin_width_is_valid(mdl):
    if not mdl.mag_bin_width > 0.0:
        return False, ['Magnitude bin width must be > 0.0']
    return True, []


def distance_bin_width_is_valid(mdl):
    if not mdl.distance_bin_width > 0.0:
        return False, ['Distance bin width must be > 0.0']
    return True, []


def coordinate_bin_width_is_valid(mdl):
    if not mdl.coordinate_bin_width > 0.0:
        return False, ['Coordinate bin width must be > 0.0']
    return True, []


def num_epsilon_bins_is_valid(mdl):
    if not mdl.num_epsilon_bins > 0:
        return False, ['Number of epsilon bins must be > 0']
    return True, []


def asset_life_expectancy_is_valid(mdl):
    if mdl.is_bcr:
        if mdl.asset_life_expectancy is None or mdl.asset_life_expectancy <= 0:
            return False, ['Asset Life Expectancy must be > 0']
    return True, []


def interest_rate_is_valid(mdl):
    if mdl.is_bcr:
        if mdl.interest_rate is None or mdl.interest_rate <= 0:
            return False, ['Interest Rate must be > 0']
    return True, []


def insured_losses_is_valid(_mdl):
    # The validation form should normalize the type to a boolean.
    # We don't need to check anything here.
    return True, []


def loss_curve_resolution_is_valid(mdl):
    if mdl.calculation_mode == 'event_based':
        if (mdl.loss_curve_resolution is not None and
                mdl.loss_curve_resolution < 1):
            return False, ['Loss Curve Resolution must be > 1.']
    return True, []


def asset_correlation_is_valid(_mdl):
    # The validation form should check if it is in the list
    # We don't need to check anything here.
    if _mdl.asset_correlation is not None:
        if not (_mdl.asset_correlation >= 0 and _mdl.asset_correlation <= 1):
            return False, ['Asset Correlation must be >= 0 and <= 1']
    return True, []


def master_seed_is_valid(_mdl):
    return True, []


def gsim_is_valid(mdl):
    if mdl.gsim in AVAILABLE_GSIMS:
        return True, []
    return False, ['The gsim %r is not in in nhlib.gsim' % mdl.gsim]


def number_of_ground_motion_fields_is_valid(mdl):
    gmfno = mdl.number_of_ground_motion_fields
    if gmfno > 0:
        return True, []
    return False, ['The number_of_ground_motion_fields must be a positive '
                   'integer, got %r' % gmfno]


def poes_disagg_is_valid(mdl):
    poesd = mdl.poes_disagg
    if len(poesd) == 0:
        return False, ['`poes_disagg` must contain at least 1 value']
    error_msg = 'PoEs for disaggregation must be in the range [0, 1]'
    return _validate_poe_list(poesd, error_msg)
