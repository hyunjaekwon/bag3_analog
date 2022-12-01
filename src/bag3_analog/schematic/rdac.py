# BSD 3-Clause License
#
# Copyright (c) 2018, Regents of the University of California
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# * Redistributions of source code must retain the above copyright notice, this
#   list of conditions and the following disclaimer.
#
# * Redistributions in binary form must reproduce the above copyright notice,
#   this list of conditions and the following disclaimer in the documentation
#   and/or other materials provided with the distribution.
#
# * Neither the name of the copyright holder nor the names of its
#   contributors may be used to endorse or promote products derived from
#   this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

# -*- coding: utf-8 -*-

from typing import Mapping, Any

import pkg_resources
from pathlib import Path

from bag.design.module import Module
from bag.design.database import ModuleDB
from bag.util.immutable import Param

from pybag.enum import TermType


# noinspection PyPep8Naming
class bag3_analog__rdac(Module):
    """Module for library bag3_analog cell rdac.

    Fill in high level description here.
    """

    yaml_file = pkg_resources.resource_filename(__name__,
                                                str(Path('netlist_info',
                                                         'rdac.yaml')))

    def __init__(self, database: ModuleDB, params: Param, **kwargs: Any) -> None:
        Module.__init__(self, self.yaml_file, database, params, **kwargs)

    @classmethod
    def get_params_info(cls) -> Mapping[str, str]:
        """Returns a dictionary from parameter names to descriptions.

        Returns
        -------
        param_info : Optional[Mapping[str, str]]
            dictionary from parameter names to descriptions.
        """
        return dict(
            res_params='Parameters for res_ladder',
            dec_params='Parameters for rdac_decoder',
            num_dec='Number of decoders for one res_ladder',
        )

    @classmethod
    def get_default_param_values(cls) -> Mapping[str, Any]:
        return dict(num_dec=1)

    def design(self, res_params: Mapping[str, Any], dec_params: Mapping[str, Any], num_dec: int) -> None:
        """To be overridden by subclasses to design this module.

        This method should fill in values for all parameters in
        self.parameters.  To design instances of this module, you can
        call their design() method or any other ways you coded.

        To modify schematic structure, call:

        rename_pin()
        delete_instance()
        replace_instance_master()
        reconnect_instance_terminal()
        restore_instance()
        array_instance()
        """
        self.instances['XDEC'].design(**dec_params)
        num_sel_row: int = dec_params['row_params']['num_sel']
        num_sel_col: int = dec_params['col_params']['num_sel']
        num_sel = num_sel_col + num_sel_row
        sel_suf = f'<{num_sel - 1}:0>'
        num_in = 1 << num_sel
        sel_pin = f'sel{sel_suf}'

        self.instances['XRES'].design(**res_params)
        # Check if ladder has idx0
        has_idx0 = self.instances['XRES'].master.has_idx0
        if has_idx0:
            _suf = f'<{num_in - 1}:0>'
            res_term = f'out{_suf}'
            dec_net = dec_term = res_net = f'in{_suf}'
        else:
            dec_suf = f'<{num_in - 1}:0>' 
            res_suf = f'<{num_in - 1}:1>'
            bot_name = "VSS" if self.instances['XRES'].master.bot_vss else "bottom"
            
            res_term = f'out{res_suf}'
            res_net = f'in{res_suf}'
            dec_term = f'in{dec_suf}'
            dec_net = f'{res_net},{bot_name}'

        self.reconnect_instance('XRES', [(res_term, res_net), ('VDD', 'VDD'), ('VSS', 'VSS')])

        if num_dec == 2:
            sel0_pin = f'sel0{sel_suf}'
            sel1_pin = f'sel1{sel_suf}'
            self.rename_pin('sel', sel0_pin)
            self.add_pin(sel1_pin, TermType.input)

            self.rename_pin('out', 'out0')
            self.add_pin('out1', TermType.output)

            self.array_instance('XDEC', inst_term_list=[('XDEC0', [(sel_pin, sel0_pin), (dec_term, dec_net),
                                                                   ('out', 'out0')]),
                                                        ('XDEC1', [(sel_pin, sel1_pin), (dec_term, dec_net),
                                                                   ('out', 'out1')])])
        elif num_dec == 1:
            self.rename_pin('sel', sel_pin)
            self.reconnect_instance('XDEC', [(sel_pin, sel_pin), (dec_term, dec_net)])
        else:
            raise ValueError(f'num_dec={num_dec} is not supported yet. Use 1 or 2.')


