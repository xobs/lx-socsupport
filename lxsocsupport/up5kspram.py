# This file is Copyright (c) 2019 William D. Jones <thor0505@comcast.net>
# This file is Copyright (c) 2019 Tim 'mithro' Ansell <me@mith.ro>
# This file is Copyright (c) 2019 Florent Kermarrec <florent@enjoy-digital.fr>
# License: BSD

from migen import *
from litex.soc.interconnect import wishbone

kB = 1024

"""
ICE40 UltraPlus family-specific Wishbone interface to the Single Port RAM (SPRAM) primitives.
Because SPRAM is much more coarse grained than Block RAM resources, this RAM is only minimally
configurable (16 or 32-bit and 64kB, 128kB or 256kB). Because it is single port, this module is
meant to be used as the CPU's RAM region, leaving block RAM free for other use.

Example: To get a 32-bit data bus, we must width-cascade 2 16-bit SPRAMs. We've already used 2 out
of 4 SPRAMs for this, so the only other valid config is using all 4 SPRAMs by depth-cascading.

"""

class Up5kSPRAM(Module):
    def __init__(self, width=32, size=64*kB):
        assert width in [16, 32]
        if width == 16:
            assert size in [64*kB, 128*kB, 256*kB]
        if width == 32:
            assert size in [64*kB, 128*kB]

        self.bus = wishbone.Interface(width)

        for d in range(size//(64*kB)): # depth-cascading loop
            for w in range(width//16): # width-cascading loop
                print(w)
                datain = Signal(16)
                dataout = Signal(16)
                maskwren = Signal(4)
                wren = Signal()
                self.comb += [
                    datain.eq(self.bus.dat_w[16*w:16*(w+1)]),
                    If(self.bus.adr[14:16] == d,
                        wren.eq(self.bus.we & self.bus.stb & self.bus.cyc),
                        self.bus.dat_r[16*w:16*(w+1)].eq(dataout)
                    ),
                    # maskwren is nibble based
                    maskwren[0].eq(self.bus.sel[2*w + 0]),
                    maskwren[1].eq(self.bus.sel[2*w + 0]),
                    maskwren[2].eq(self.bus.sel[2*w + 1]),
                    maskwren[3].eq(self.bus.sel[2*w + 1]),
                ]
                self.specials += Instance("SB_SPRAM256KA",
                    i_ADDRESS=self.bus.adr[:14],
                    i_DATAIN=datain,
                    i_MASKWREN=maskwren,
                    i_WREN=wren,
                    i_CHIPSELECT=0b1,
                    i_CLOCK=ClockSignal("sys"),
                    i_STANDBY=0b0,
                    i_SLEEP=0b0,
                    i_POWEROFF=0b1,
                    o_DATAOUT=dataout
                )

        self.sync += [
            self.bus.ack.eq(0),
            If(self.bus.stb & self.bus.cyc & ~self.bus.ack,
                self.bus.ack.eq(1)
            )
        ]
