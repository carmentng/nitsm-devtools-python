import re
import typing
import numpy
import niscope
from nitsm.codemoduleapi import SemiconductorModuleContext
from nitsm.pinquerycontexts import PinQueryContext
from enum import Enum


class SSCScope(typing.NamedTuple):
    session: niscope.Session
    channels: str
    channel_list: str


class TSMScope(typing.NamedTuple):
    pin_query_context: typing.Any
    site_numbers: typing.List[int]
    ssc: typing.List[SSCScope]


class PinType(Enum):
    DUT_Pin = 0
    System_Pin = 1
    Pin_Group = 2
    Not_Determined = 3


class ExpandedPinInformation(typing.NamedTuple):
    Pin: str
    Type: PinType
    Index: int


class PinsCluster(typing.NamedTuple):
    Pins: typing.List[str]


class ScopeSessionProperties(typing.NamedTuple):
    instrument_name: str
    channel: str
    pin: str
    voltage_range: float
    coupling: str
    attenuation: float
    sampling_rate: float
    input_impedance: float
    trigger_channel: str
    edge: str


class OutputTerminal(typing.NamedTuple):
    NONE: str
    PXI_trigger_line0_RTSI0: str
    PXI_trigger_line1_RTSI1: str
    PXI_trigger_line2_RTSI2: str
    PXI_trigger_line3_RTSI3: str
    PXI_trigger_line4_RTSI4: str
    PXI_trigger_line5_RTSI5: str
    PXI_trigger_line6_RTSI6: str
    PXI_trigger_line7_RTSI7_RTSI_clock: str
    PXI_star_trigger: str
    PFI0: str
    PFI1: str
    PFI2: str
    PFI3: str
    PFI4: str
    PFI5: str
    PFI6: str
    PFI7: str
    Clock_out: str
    AUX0_PFI0: str
    AUX0_PFI1: str
    AUX0_PFI2: str
    AUX0_PFI3: str
    AUX0_PFI4: str
    AUX0_PFI5: str
    AUX0_PFI6: str
    AUX0_PFI7: str


OUTPUT_TERMINAL = OutputTerminal(
    "VAL_NO_SOURCE",
    "VAL_RTSI_0",
    "VAL_RTSI_1",
    "VAL_RTSI_2",
    "VAL_RTSI_3",
    "VAL_RTSI_4",
    "VAL_RTSI_5",
    "VAL_RTSI_6",
    "VAL_RTSI_7",
    "VAL_PXI_STAR",
    "VAL_PFI_0",
    "VAL_PFI_1",
    "VAL_PFI_2",
    "VAL_PFI_3",
    "VAL_PFI_4",
    "VAL_PFI_5",
    "VAL_PFI_6",
    "VAL_PFI_7",
    "VAL_CLK_OUT",
    "VAL_AUX_0_PFI_0",
    "VAL_AUX_0_PFI_1",
    "VAL_AUX_0_PFI_2",
    "VAL_AUX_0_PFI_3",
    "VAL_AUX_0_PFI_4",
    "VAL_AUX_0_PFI_5",
    "VAL_AUX_0_PFI_6",
    "VAL_AUX_0_PFI_7",
)


class TriggerSource(typing.NamedTuple):
    RTSI0: str
    RTSI1: str
    RTSI2: str
    RTSI3: str
    RTSI4: str
    RTSI5: str
    RTSI6: str
    PFI0: str
    PFI1: str
    PFI2: str
    PFI3: str
    PFI4: str
    PFI5: str
    PFI6: str
    PFI7: str
    PXI_star_trigger: str
    AUX0_PFI0: str
    AUX0_PFI1: str
    AUX0_PFI2: str
    AUX0_PFI3: str
    AUX0_PFI4: str
    AUX0_PFI5: str
    AUX0_PFI6: str
    AUX0_PFI7: str


TRIGGER_SOURCE = TriggerSource(
    "VAL_RTSI_0",
    "VAL_RTSI_1",
    "VAL_RTSI_2",
    "VAL_RTSI_3",
    "VAL_RTSI_4",
    "VAL_RTSI_5",
    "VAL_RTSI_6",
    "VAL_PFI_0",
    "VAL_PFI_1",
    "VAL_PFI_2",
    "VAL_PFI_3",
    "VAL_PFI_4",
    "VAL_PFI_5",
    "VAL_PFI_6",
    "VAL_PFI_7",
    "VAL_PXI_STAR",
    "VAL_AUX_0_PFI_0",
    "VAL_AUX_0_PFI_1",
    "VAL_AUX_0_PFI_2",
    "VAL_AUX_0_PFI_3",
    "VAL_AUX_0_PFI_4",
    "VAL_AUX_0_PFI_5",
    "VAL_AUX_0_PFI_6",
    "VAL_AUX_0_PFI_7",
)


# Scope Sub routines


def _expand_ssc_to_ssc_per_channel(ssc: typing.List[SSCScope]):
    return [
        SSCScope(scope_ssc.session, channel, channel_list)
        for scope_ssc in ssc
        for channel, channel_list in zip(
            re.split(r"\s*,\s*", scope_ssc.channels),
            re.split(r"\s*,\s*", scope_ssc.channel_list),
        )
    ]


def _ssc_scope_configure_vertical_per_channel_arrays(
    ssc: typing.List[SSCScope],
    vertical_ranges: typing.List[float],
    vertical_offsets: typing.List[float],
    vertical_couplings: typing.List[niscope.VerticalCoupling],
    probes_attenuation: typing.List[float],
    channels_enabled: typing.List[bool],
):
    for (
        scope_ssc,
        vertical_range,
        vertical_offset,
        vertical_coupling,
        probe_attenuation,
        channel_enabled,
    ) in zip(
        ssc,
        vertical_ranges,
        vertical_offsets,
        vertical_couplings,
        probes_attenuation,
        channels_enabled,
    ):
        scope_ssc.session.channels[scope_ssc.channels].configure_vertical(
            vertical_range,
            vertical_coupling,
            vertical_offset,
            probe_attenuation,
            channel_enabled,
        )


def _ssc_scope_fetch_measurement_stats_arrays(
    ssc: typing.List[SSCScope],
    scalar_measurements: typing.List[niscope.ScalarMeasurement],
):
    stats: typing.List[niscope.MeasurementStats] = []
    for scope_ssc, scalar_meas_function in zip(ssc, scalar_measurements):
        stats.append(
            scope_ssc.session.channels[scope_ssc.channels].fetch_measurement_stats(
                scalar_meas_function
            )
        )  # function with unknown type
    return stats


def _ssc_scope_obtain_trigger_path(tsm: TSMScope, trigger_source: str, setup_type: str):
    trigger_paths: typing.List[str] = []
    if setup_type == "STSM1":
        for ssc in tsm.ssc:
            chassis_string = re.match(
                r"_C[1-4]_", ssc.session.io_resource_descriptor
            ).group()
            timing_card = "SYNC_6674T_C{}_S10".format(chassis_string[2])
            trigger_path = "/" + timing_card + "/" + "PFI0"
            trigger_paths.append(trigger_path)
    else:
        for ssc in tsm.ssc:
            trigger_paths.append(trigger_source)
    return trigger_paths


# TSM Pin Abstraction Sub routines


def _pin_query_context_to_channel_list(
    expanded_pins_information: typing.List[ExpandedPinInformation],
    site_numbers: typing.List[int],
    pin_query_context: PinQueryContext,
    tsm_context: SemiconductorModuleContext,
):
    pins_array_for_session_input: typing.List[PinsCluster] = []
    channel_list_per_session = ()
    pin_types_return: typing.List[PinType] = []
    pin_names_return: typing.Union[str, typing.Sequence[str]] = []
    pins: typing.Union[str, typing.Sequence[str]] = pin_query_context._pins
    (
        number_of_pins_per_channel,
        channel_group_indices,
        channel_indices,
    ) = pin_query_context.get_channel_group_and_channel_index(pins)
    for number_of_pins in number_of_pins_per_channel:
        """
        Create a pins list for each session of the correct size
        """
        initialized_pins: typing.List[str] = [""] * number_of_pins
        pins_array_for_session_input.append(PinsCluster(Pins=initialized_pins))
    if len(site_numbers) == 0:
        """
        Get site numbers if not provided
        """
        site_numbers_out: typing.List[int] = list(tsm_context.site_numbers)
    else:
        site_numbers_out = site_numbers
    if len(expanded_pins_information) == 0:
        """
        The list of pins from Pin Query Context Read Pins
        doesn't expand pin groups, it only contains the
        initial strings provided to pins to sessions

        If a pin group is found when identifying pin types,
        expand pin groups
        """
        pin_types_return, pin_names_return = _check_for_pin_group(tsm_context, pins)
    else:
        for expanded_pin_information in expanded_pins_information:
            pin_names_return.append(expanded_pin_information.Pin)
            pin_types_return.append(expanded_pin_information.Type)
    for (
        per_site_transposed_channel_group_indices,
        per_site_transposed_channel_indices,
        site_number,
    ) in zip(
        numpy.transpose(channel_group_indices),
        numpy.transpose(channel_indices),
        site_numbers_out,
    ):
        for (
            per_pin_transposed_channel_group_index,
            per_pin_transposed_channel_index,
            pin,
            pin_type,
        ) in zip(
            per_site_transposed_channel_group_indices,
            per_site_transposed_channel_indices,
            pin_names_return,
            pin_types_return,
        ):
            if pin_type.value == 1:
                pins_array_for_session_input[
                    per_pin_transposed_channel_group_index
                ].Pins[per_pin_transposed_channel_index] = pin
            else:
                pins_array_for_session_input[
                    per_pin_transposed_channel_group_index
                ].Pins[per_pin_transposed_channel_index] = "Site{}/{}".format(
                    site_number, pin
                )
    for pins_array_for_session in pins_array_for_session_input:
        channel_list = ",".join(pins_array_for_session.Pins)
        channel_list_per_session += (channel_list,)
    return site_numbers_out, channel_list_per_session


def _check_for_pin_group(
    tsm_context: SemiconductorModuleContext,
    pins_or_pins_group: typing.Union[str, typing.Sequence[str]],
):
    pins_types, pin_group_found = _identify_pin_types(tsm_context, pins_or_pins_group)
    if pin_group_found == True:
        pins: typing.Union[
            str, typing.Sequence[str]
        ] = tsm_context.get_pins_in_pin_group(pins_or_pins_group)
        pins_types, _ = _identify_pin_types(tsm_context, pins)
    else:
        pins = pins_or_pins_group
    return pins_types, pins


def _identify_pin_types(
    tsm_context: SemiconductorModuleContext,
    pins_or_pins_group: typing.Union[str, typing.Sequence[str]],
):
    filtered_pin_types: typing.List[PinType] = []
    pin_group_found: bool = False
    pin_names, pin_types = _get_all_pin_names(tsm_context, reload_cache=False)
    for pin in pins_or_pins_group:
        try:
            index = pin_names.index(pin)
            filtered_pin_types.append(pin_types[index])
            pin_group_found = False
        except ValueError:
            index = -1
            filtered_pin_types.append(PinType.Pin_Group)
            pin_group_found = True
    return filtered_pin_types, pin_group_found


def _get_all_pin_names(
    tsm_context: SemiconductorModuleContext,
    reload_cache: bool = False,
):
    pin_names: typing.Union[str, typing.Sequence[str]] = []
    pin_types: typing.List[PinType] = []
    if len(pin_names) == 0 or reload_cache == True:
        dut_pins, system_pins = tsm_context.get_pin_names("", "")
        dut_pins_type = [PinType.DUT_Pin] * len(dut_pins)
        system_pins_type = [PinType.System_Pin] * len(system_pins)
        pin_names = dut_pins + system_pins
        pin_types = dut_pins_type + system_pins_type
    return pin_names, pin_types


# Digital Sub routines


def _channel_list_to_pins(channel_list: str):
    channels = re.split(r"\s*,\s*", channel_list)
    sites = [-1] * len(channels)
    pins = channels[:]
    for i in range(len(channels)):
        try:
            site, pins[i] = re.split(r"[/\\]", channels[i])
        except ValueError:
            pass
        else:
            sites[i] = int(re.match(r"Site(\d+)", site).group(1))
    return channels, pins, sites


# DCPower Sub routines


def _expand_to_requested_array_size(
    data_in: typing.Any,
    requested_size: int,
):
    i = 0
    data: typing.Any
    data_out: typing.Any = []
    if isinstance(data_in, tuple):
        i = 0
        data = data_in
        for _ in range(requested_size):
            data_out.append(data[i])
            if i == len(data):
                i = 0
            else:
                i += 1
    else:
        data = (data_in,)
        data_out = data * requested_size
    if (len(data) == 0 ^ requested_size == 0) or (requested_size % len(data) != 0):
        if len(data) == 0 or requested_size == 0:
            raise ValueError("Empty array input")
        else:
            raise ValueError("Input array does not evenly distribute into sessions")
    return data_out


# Pinmap


def tsm_ssc_scope_pins_to_sessions(
    tsm_context: SemiconductorModuleContext,
    pins: typing.List[str],
    site_numbers: typing.List[int],
):
    ssc: typing.List[SSCScope] = []
    pin_query_context, sessions, channels = tsm_context.pins_to_niscope_sessions(pins)
    site_numbers_out, channel_list_per_session = _pin_query_context_to_channel_list(
        [], site_numbers, pin_query_context, tsm_context
    )
    for session, channel, channel_list in zip(
        sessions, channels, channel_list_per_session
    ):
        ssc.append(
            SSCScope(session=session, channels=channel, channel_list=channel_list)
        )
    return TSMScope(pin_query_context, site_numbers_out, ssc)


# Configure


def configure_impedance(tsm: TSMScope, input_impedance: float):
    for ssc in tsm.ssc:
        ssc.session.channels[ssc.channels].configure_chan_characteristics(
            input_impedance, -1.0
        )
    return tsm


def configure_reference_level(tsm: TSMScope):
    for ssc in tsm.ssc:
        channels = ssc.session.channels[ssc.channels]
        channels.meas_ref_level_units = niscope.RefLevelUnits.PERCENTAGE
        channels.meas_chan_mid_ref_level = 50.0
        channels.meas_percentage_method = niscope.PercentageMethod.BASETOP
    return tsm


def configure_vertical(
    tsm: TSMScope,
    vertical_range: float,
    vertical_offset: float,
    vertical_coupling: niscope.VerticalCoupling,
    probe_attenuation: float,
    channel_enabled: bool,
):
    for ssc in tsm.ssc:
        ssc.session.channels[ssc.channels].configure_vertical(
            vertical_range,
            vertical_coupling,
            vertical_offset,
            probe_attenuation,
            channel_enabled,
        )
    return tsm


def configure(
    tsm: TSMScope,
    vertical_range: float = 5.0,
    probe_attenuation: float = 1.0,
    vertical_offset: float = 0.0,
    vertical_coupling: niscope.VerticalCoupling = niscope.VerticalCoupling.DC,
    min_sample_rate: float = 10e6,
    min_record_length: int = 1000,
    ref_position: float = 0.0,
    max_input_frequency: float = 0.0,
    input_impedance: float = 1e6,
    num_records: int = 1,
    enforce_realtime: bool = True,
):
    for ssc in tsm.ssc:
        channels = ssc.session.channels[ssc.channels]
        channels.configure_vertical(
            vertical_range, vertical_coupling, vertical_offset, probe_attenuation
        )
        channels.configure_chan_characteristics(input_impedance, max_input_frequency)
        ssc.session.configure_horizontal_timing(
            min_sample_rate,
            min_record_length,
            ref_position,
            num_records,
            enforce_realtime,
        )
    return tsm


def configure_vertical_per_channel(
    tsm: TSMScope,
    vertical_range: float,
    vertical_offset: float,
    vertical_coupling: niscope.VerticalCoupling,
    probe_attenuation: float,
    channel_enabled: bool,
):
    scope_ssc_per_channel = _expand_ssc_to_ssc_per_channel(tsm.ssc)
    probe_attenuation_out = _expand_to_requested_array_size(
        probe_attenuation, len(scope_ssc_per_channel)
    )
    vertical_coupling_out = _expand_to_requested_array_size(
        vertical_coupling, len(scope_ssc_per_channel)
    )
    vertical_range_out = _expand_to_requested_array_size(
        vertical_range, len(scope_ssc_per_channel)
    )
    vertical_offset_out = _expand_to_requested_array_size(
        vertical_offset, len(scope_ssc_per_channel)
    )
    channel_enabled_out = _expand_to_requested_array_size(
        channel_enabled, len(scope_ssc_per_channel)
    )
    _ssc_scope_configure_vertical_per_channel_arrays(
        scope_ssc_per_channel,
        vertical_range_out,
        vertical_offset_out,
        vertical_coupling_out,
        probe_attenuation_out,
        channel_enabled_out,
    )
    return tsm


# Configure Timing


def configure_timing(
    tsm: TSMScope,
    min_sample_rate: float,
    min_num_pts: int,
    ref_position: float,
    num_records: int,
    enforce_realtime: bool,
):
    for ssc in tsm.ssc:
        ssc.session.configure_horizontal_timing(
            min_sample_rate,
            min_num_pts,
            ref_position,
            num_records,
            enforce_realtime,
        )
    return tsm


# Acquisition


def initiate(tsm: TSMScope):
    for ssc in tsm.ssc:
        ssc.session.initiate()
    return tsm


# Control


def abort(tsm: TSMScope):
    for ssc in tsm.ssc:
        ssc.session.abort
    return tsm


def commit(tsm: TSMScope):
    for ssc in tsm.ssc:
        ssc.session.commit
    return tsm


# Session Properties


def scope_get_session_properties(tsm: TSMScope):
    instrument_name: str
    voltage_range: float
    attenuation: float
    sampling_rate: float
    input_impedance: float
    trigger_channel: str
    ScopeProperties: typing.List[ScopeSessionProperties] = []
    for ssc in tsm.ssc:
        instrument_name = ssc.session.io_resource_descriptor
        pin = ssc.channel_list
        channel = ssc.channels
        voltage_range = ssc.session.channels[ssc.channels].vertical_range
        attenuation = ssc.session.channels[ssc.channels].probe_attenuation
        sampling_rate = ssc.session.horz_sample_rate
        input_impedance = ssc.session.channels[ssc.channels].input_impedance
        if ssc.session.channels[ssc.channels].vertical_coupling.value == 0:
            coupling = "AC"
        elif ssc.session.channels[ssc.channels].vertical_coupling.value == 1:
            coupling = "DC"
        elif ssc.session.channels[ssc.channels].vertical_coupling.value == 2:
            coupling = "Ground"
        else:
            coupling = "Unsupported"
        trigger_channel = ssc.session.trigger_source
        if ssc.session.trigger_slope.value == 0:
            edge = "Negative"
        elif ssc.session.trigger_slope.value == 1:
            edge = "Positive"
        else:
            edge = "Unsupported"
        ScopeProperties.append(
            ScopeSessionProperties(
                instrument_name,
                channel,
                pin,
                voltage_range,
                coupling,
                attenuation,
                sampling_rate,
                input_impedance,
                trigger_channel,
                edge,
            )
        )
    return tsm, ScopeProperties


# Trigger


def scope_configure_digital_edge_trigger(
    tsm: TSMScope,
    trigger_source: str,
    slope: niscope.TriggerSlope,
    holdoff: float = 0.0,
    delay: float = 0.0,
):
    for ssc in tsm.ssc:
        ssc.session.configure_trigger_digital(
            trigger_source,
            slope,
            holdoff,
            delay,
        )
        ssc.session.trigger_modifier = niscope.TriggerModifier.NO_TRIGGER_MOD
    return tsm


def scope_configure_trigger(
    tsm: TSMScope,
    level: float,
    trigger_coupling: niscope.TriggerCoupling,
    slope: niscope.TriggerSlope,
    holdoff: float = 0.0,
    delay: float = 0.0,
):
    for ssc in tsm.ssc:
        ssc.session.configure_trigger_edge(
            ssc.channels,
            level,
            trigger_coupling,
            slope,
            holdoff,
            delay,
        )
    return tsm


def tsm_ssc_scope_clear_triggers(tsm: TSMScope):
    for ssc in tsm.ssc:
        ssc.session.abort()
        ssc.session.configure_trigger_immediate()
        ssc.session.exported_start_trigger_output_terminal = OUTPUT_TERMINAL.NONE
        ssc.session.commit()
    return tsm


def tsm_ssc_scope_export_start_triggers(tsm: TSMScope, output_terminal: str):
    start_trigger: str = ""
    if tsm.ssc != []:
        for ssc in tsm.ssc:
            if tsm.ssc.index(ssc) == 0:
                ssc.session.configure_trigger_immediate()
                ssc.session.exported_start_trigger_output_terminal = output_terminal
                ssc.session.commit()
                start_trigger = (
                    "/" + ssc.session.io_resource_descriptor + "/" + output_terminal
                )
            else:
                ssc.session.configure_trigger_digital(
                    start_trigger,
                    niscope.TriggerSlope.POSITIVE,
                    holdoff=0.0,
                    delay=0.0,
                )
                ssc.session.initiate()
    return tsm, start_trigger


def tsm_ssc_scope_start_acquisition(tsm: TSMScope):
    for ssc in reversed(tsm.ssc):
        ssc.session.abort()
        ssc.session.initiate()
    return tsm


# Measure


def scope_fetch_measurement(
    tsm: TSMScope,
    scalar_meas_function: niscope.ScalarMeasurement,
):
    measurements: typing.List[float] = []
    for ssc in tsm.ssc:
        measurement_stats = ssc.session.channels[ssc.channels].fetch_measurement_stats(
            scalar_meas_function, num_records=1
        )  # Single channel and record
        for measurement_stat in measurement_stats:
            measurements.append(measurement_stat.result)
    return tsm, measurements


def scope_fetch_waveform(
    tsm: TSMScope,
    meas_num_samples: int,
):
    waveforms: typing.Any = []
    waveform_info: typing.List[niscope.WaveformInfo] = []
    for ssc in tsm.ssc:
        channels, pins, sites = _channel_list_to_pins(
            ssc.channel_list
        )  # Unused no waveform attribute in python
        waveform = ssc.session.channels[ssc.channels].fetch(
            meas_num_samples, relative_to=niscope.FetchRelativeTo.PRETRIGGER
        )
        waveform_info.append(waveform)
        for wfm in waveform:
            waveforms.append(list(wfm.samples))  # waveform in memoryview
    return tsm, waveform_info, waveforms


def scope_measure_statistics(
    tsm: TSMScope,
    scalar_meas_function: niscope.ScalarMeasurement,
):
    measurement_stats: typing.List[niscope.MeasurementStats] = []
    for ssc in tsm.ssc:
        ssc.session.channels[ssc.channels].clear_waveform_measurement_stats(
            clearable_measurement_function=niscope.ClearableMeasurement.ALL_MEASUREMENTS
        )
        ssc.session.initiate()
        measurement_stats.append(
            ssc.session.channels[ssc.channels].fetch_measurement_stats(
                scalar_meas_function
            )
        )
    return tsm, measurement_stats


def ssc_scope_fetch_clear_stats(ssc: typing.List[SSCScope]):
    for scope_ssc in ssc:
        scope_ssc.session.channels[scope_ssc.channels].clear_waveform_measurement_stats(
            clearable_measurement_function=niscope.ClearableMeasurement.ALL_MEASUREMENTS
        )
    return ssc


def tsm_ssc_scope_fetch_meas_stats_per_channel(
    tsm: TSMScope,
    scalar_measurement: niscope.ScalarMeasurement,
):
    scope_ssc_per_channel = _expand_ssc_to_ssc_per_channel(tsm.ssc)
    scalar_measurements = _expand_to_requested_array_size(
        scalar_measurement, len(scope_ssc_per_channel)
    )
    measurement_stats = _ssc_scope_fetch_measurement_stats_arrays(
        scope_ssc_per_channel, scalar_measurements
    )
    return tsm, measurement_stats


# Open session


def tsm_scope_initialize_sessions(
    tsm_context: SemiconductorModuleContext, options_input: str
):
    instrument_names = tsm_context.get_all_niscope_instrument_names()
    for instrument_name in instrument_names:
        session = niscope.Session(
            instrument_name, reset_device=True, options=options_input
        )
        try:
            session.commit()
        except:
            session.reset_device()
        session.channels[0, 1].configure_chan_characteristics(1e6, -1)
        session.commit()
        tsm_context.set_niscope_session(instrument_name, session)


# Close session


def tsm_scope_close_sessions(tsm_context: SemiconductorModuleContext):
    sessions = tsm_context.get_all_niscope_sessions()
    for session in sessions:
        session.reset()
        session.close()
