from fractions import Fraction
from typing import Optional

from vapoursynth import Error, VideoNode

from vsfieldkit.types import FormatSpecifier, Resizer
from vsfieldkit.util import convert_format_if_needed

BT601_SAMPLE_RATE = 13_500_000
NTSC_SUBCARRIER_FREQ = 5_000_000 * Fraction(63, 88)
NTSC_LINE_FREQ = Fraction(2, 455) * NTSC_SUBCARRIER_FREQ
NTSC_FIELD_FREQ = Fraction(2, 525) * NTSC_LINE_FREQ
NTSC_LINE_TIME = 1 / NTSC_LINE_FREQ

NTSC_170M_LEAD_BLANKING_TIME = Fraction(1_500, 1000000000)
NTSC_170M_TAIL_BLANKING_TIME = Fraction(9_200, 1000000000)
NTSC_170M_LINE_BLANKING_TIME = (
    NTSC_170M_LEAD_BLANKING_TIME
    + NTSC_170M_TAIL_BLANKING_TIME
)
NTSC_170M_LINE_ACTIVE_TIME = NTSC_LINE_TIME - NTSC_170M_LINE_BLANKING_TIME
NTSC_170M_ACTIVE_BT601_SAMPLES = (
    # Fraction(14271, 20) or 713.55
    NTSC_170M_LINE_ACTIVE_TIME
    * BT601_SAMPLE_RATE
)

NTSC_BT470_LINE_BLANKING_TIME = Fraction(10_900, 1000000000)
NTSC_BT470_LINE_ACTIVE_TIME = (
    NTSC_LINE_TIME
    - NTSC_BT470_LINE_BLANKING_TIME
)
NTSC_BT470_LINE_ACTIVE_BT601_SAMPLES = (
    # Fraction(14217, 20) or 710.85
    NTSC_BT470_LINE_ACTIVE_TIME
    * BT601_SAMPLE_RATE
)

PAL_LINE_FREQ = 15_625
PAL_SUBCARRIER_FREQ = (
    Fraction(1135, 4)
    + Fraction(1, 625)
) * PAL_LINE_FREQ
PAL_SUBCARRIER_FREQ_ARGENTINA = (
    Fraction(917, 4)
    + Fraction(1, 625)
)
# fOR = 282 * PAL_LINE_FREQ
# fOB = 272 * PAL_LINE_FREQ
PAL_LINE_TIME = Fraction(1, PAL_LINE_FREQ)
PAL_LINE_BLANKING_TIME = Fraction(12_000, 1000000000)
PAL_LINE_ACTIVE_TIME = PAL_LINE_TIME - PAL_LINE_BLANKING_TIME
PAL_ACTIVE_BT601_SAMPLES = (
    # 702
    PAL_LINE_ACTIVE_TIME
    * BT601_SAMPLE_RATE
)
NTSC_4FSC = 4 * NTSC_SUBCARRIER_FREQ
NTSC_4FSC_ACTIVE_WIDTH = NTSC_4FSC * NTSC_170M_LINE_ACTIVE_TIME
# Fraction(33299, 44) or 756.7954545454545
NTSC_4FSC_ACTIVE_HEIGHT = 486  # TODO: exact

PAL_4FSC = 4 * PAL_SUBCARRIER_FREQ
PAL_4FSC_ACTIVE_WIDTH = PAL_4FSC * PAL_LINE_ACTIVE_TIME 
#  Fraction(9221927, 10000) or 922.1927
# A certain tool uses 928, because mod-8.

def resample_bt601_as_4fsc(
    clip: VideoNode,
    format: Optional[FormatSpecifier],
    kernel: Resizer,
    **format_resize_args
) -> VideoNode:
    """Takes a clip sampled from analog video according to the BT.601 spec
    and generates new video as if sampled at four times the color sub-carrier
    frequency (4fSC) instead. Optionally will change the sample format in the
    same transformation.
    """
    if clip.width != 720:
        raise Error('Only full active BT.601 width (720 samples) is supported')

    if clip.height == 576:
        src_active_width = PAL_ACTIVE_BT601_SAMPLES
        # PAL isn't cropped for compression.
        src_original_top = None
    elif clip.height == 480:
        src_active_width = NTSC_170M_ACTIVE_BT601_SAMPLES
        # Assume vertical RP 202 crop for compression.
        # This is 5 lines below the 486i start.
        src_original_top = -5
        src_original_height = 486
    elif clip.height == 486:
        src_active_width = NTSC_170M_ACTIVE_BT601_SAMPLES
        src_original_top = None
    else:
        raise Error('480i, 486i, or 576i height required for')

    return convert_format_if_needed(
        clip,
        format=format,
        kernel=kernel,
        src_left=float((clip.width - src_active_width) / 2),
        src_width=float(src_active_width)
    )
