# MIT license
# 
# Copyright (C) 2015 by XESS Corp.
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.


from __future__ import division
import pcbnew

import HelpfulFootprintWizardPlugin
import FootprintWizardDrawingAids
import PadArray as PA

from math import ceil, floor, sqrt


def calc_solderpaste_margin(w,h,fill):
    '''Calculate how far in to pull the paste mask to get a certain fill percentage.'''
    if fill > 0.99:
        return 0
    a = (h+w)/2.0
    b = w*h*(fill-1.0)
    c = sqrt(a**2+b)
    return int((a-c)/2.0)
    
    
class XessFpWizardDrawingAids(FootprintWizardDrawingAids.FootprintWizardDrawingAids):

    def Circle(self, x, y, r, filled=False):
        """
        Draw a circle at (x,y) of radius r

        If filled is true, the width and radius of the line will be set
        such that the circle appears filled
        """
        circle = pcbnew.EDGE_MODULE(self.module)
        start = self.TransformPoint(x, y)

        if filled:
            circle.SetWidth(int(r))
            end = self.TransformPoint(x, y + r/2)
        else:
            circle.SetWidth(self.dc['width'])
            end = self.TransformPoint(x, y + r)

        circle.SetLayer(self.dc['layer'])
        circle.SetShape(pcbnew.S_CIRCLE)
        circle.SetStartEnd(start, end)
        self.module.Add(circle)

    
class XessFpWizard(HelpfulFootprintWizardPlugin.HelpfulFootprintWizardPlugin):
    def GetParameterPageName(self, page_n):
        return self.page_order[page_n]

    def GetParameterNames(self, page_n):
        name = self.GetParameterPageName(page_n)
        return self.parameter_order[name]

    def GetParameterValues(self, page_n):
        name = self.GetParameterPageName(page_n)
        names = self.GetParameterNames(page_n)
        values = [self.parameters[name][n] for n in names]
        return map(lambda x: str(x), values)  # list elements as strings

    def GetParameterErrors(self, page_n):
        self.CheckParameters()
        name = self.GetParameterPageName(page_n)
        names = self.GetParameterNames(page_n)
        values = [self.parameter_errors[name][n] for n in names]
        return map(lambda x: str(x), values)  # list elements as strings

    def ConvertValue(self,v):
        try:
            v = float(v)
        except:
            pass
        if type(v) is float:
            if ceil(v) == floor(v):
                v = int(v)
        return v

    def SetParameterValues(self, page_n, values):
        name = self.GetParameterPageName(page_n)
        keys = self.GetParameterNames(page_n)
        for n, key in enumerate(keys):
            val = self.ConvertValue(values[n])
            #val = self.TryConvertToFloat(values[n])
            #val = values[n]
            self.parameters[name][key] = val

    def ProcessParameters(self):
        """
        Make sure the parameters we have meet whatever expectations the
        footprint wizard has of them
        """

        self.ClearErrors()
        self.CheckParameters()

        if self._ParametersHaveErrors():
            print "Cannot build footprint: Parameters have errors:"
            self._PrintParameterErrors()
            return False

        self._PrintParameterTable()
        return True

    def AddParam(self, section, param, unit, default, hint=''):
        """
        Add a parameter with some properties.

        TODO: Hints are not supported, as there is as yet nowhere to
        put them in the KiCAD interface
        """

        val = None
        if unit == self.uMM:
            val = pcbnew.FromMM(default)
        elif unit == self.uMils:
            val = pcbnew.FromMils(default)
        elif unit == self.uNatural:
            val = default
        elif unit == self.uString:
            val = str(default)
        elif unit == self.uBool:
            val = "True" if default else "False"  # ugly stringing
        else:
            print "Warning: Unknown unit type: %s" % unit
            return

        if unit in [self.uNatural, self.uBool, self.uString]:
            param = "*%s" % param  # star prefix for natural

        if section not in self.parameters:
            if not hasattr(self, 'page_order'):
                self.page_order = []
            self.page_order.append(section)
            self.parameters[section] = {}
            if not hasattr(self, 'parameter_order'):
                self.parameter_order = {}
            self.parameter_order[section] = []

        self.parameters[section][param] = val
        self.parameter_order[section].append(param)

    def GetValue(self):
        return "{}".format(self.parameters["Misc"]['*' + self.fp_name_key])

    def GetReferencePrefix(self):
        return "{}".format(self.parameters["Misc"]['*' + self.fp_ref_key])

        
class XessPeriphPckgWizard(XessFpWizard):

    def GetName(self):
        return "Edge-Pin Chips"

    def GetDescription(self):
        return "SOICs, TSSOPs, QFPs, etc."

    n_pads_per_col_key = '#Pads (Vertical)'
    n_pads_per_row_key = '#Pads (Horizontal)'
    total_width_key = 'Total Width (D)'
    total_height_key = 'Total Height (E)'
    body_width_key = 'Body Width (D1)'
    body_height_key = 'Body Height (E1)'
    col_to_col_pitch_key = 'Left-to-Right Column Pitch'
    row_to_row_pitch_key = 'Top-to-Bottom Row Pitch'
    pad_pitch_key = 'Pitch (e)'
    pad_width_key = 'Width (b)'
    pad_length_key = 'Length (L)'
    pad_extension_key = 'Extension'
    pad_oval_key = 'Oval (Y) / Rectangular (N)'
    pad_smd_key = 'SMD (Y) / Through-Hole (N)'
    pad_drill_key = 'Drill Size'
    pad_soldermask_margin_key = 'Soldermask Margin'
    pad_paste_fill_key = 'Paste Fill (%)'
    fp_name_key = 'Footprint Name'
    fp_ref_key = 'Reference Prefix'
    land_dim_key = 'Land Pattern (Y) / Mechanical (N)'
    outline_key = 'Silkscreen Outline (%)'
    bevel_key = 'Bevel (%)'
    add_index_key = 'Add index (Y/N)'
    paddle_enable_key = 'Thermal Pad (Y/N)'
    paddle_width_key = 'Width'
    paddle_height_key = 'Height'
    paddle_orgx_key = 'Center (X)'
    paddle_orgy_key = 'Center (Y)'
    paddle_soldermask_margin_key = 'Soldermask Margin'
    paddle_paste_fill_key = 'Paste Fill (%)'

    def GenerateParameterList(self):
        self.AddParam("Package", self.n_pads_per_row_key, self.uNatural, 11)
        self.AddParam("Package", self.n_pads_per_col_key, self.uNatural, 11)
        self.AddParam("Package", self.total_width_key, self.uMM, 12)
        self.AddParam("Package", self.total_height_key, self.uMM, 12)
        self.AddParam("Package", self.body_width_key, self.uMM, 10)
        self.AddParam("Package", self.body_height_key, self.uMM, 10)
        self.AddParam("Package", self.col_to_col_pitch_key, self.uMM, 11.25)
        self.AddParam("Package", self.row_to_row_pitch_key, self.uMM, 11.25)
        self.AddParam("Pad", self.pad_smd_key, self.uBool, True)
        self.AddParam("Pad", self.pad_oval_key, self.uBool, False)
        self.AddParam("Pad", self.pad_pitch_key, self.uMM, 0.8)
        self.AddParam("Pad", self.pad_width_key, self.uMM, 0.45)
        self.AddParam("Pad", self.pad_length_key, self.uMM, 0.75)
        self.AddParam("Pad", self.pad_extension_key, self.uMM, 0.5)
        self.AddParam("Pad", self.pad_soldermask_margin_key, self.uMM, 0)
        self.AddParam("Pad", self.pad_paste_fill_key, self.uNatural, 100)
        self.AddParam("Pad", self.pad_drill_key, self.uMM, 1)
        self.AddParam("Paddle", self.paddle_enable_key, self.uBool, False)
        self.AddParam("Paddle", self.paddle_width_key, self.uMM, 0.0)
        self.AddParam("Paddle", self.paddle_height_key, self.uMM, 0.0)
        self.AddParam("Paddle", self.paddle_orgx_key, self.uMM, 0.0)
        self.AddParam("Paddle", self.paddle_orgy_key, self.uMM, 0.0)
        self.AddParam("Paddle", self.paddle_soldermask_margin_key, self.uMM, 0)
        self.AddParam("Paddle", self.paddle_paste_fill_key, self.uNatural, 70)
        self.AddParam("Misc", self.fp_name_key, self.uString, 'Footprint Name')
        self.AddParam("Misc", self.fp_ref_key, self.uString, 'U')
        self.AddParam("Misc", self.land_dim_key, self.uBool, False)
        self.AddParam("Misc", self.outline_key, self.uNatural, 0)
        self.AddParam("Misc", self.bevel_key, self.uNatural, 20)
        self.AddParam("Misc", self.add_index_key, self.uBool, False)

    def CheckParameters(self):

        # self.CheckParamInt("Pad", '*'+self.n_pads_per_row_key)
        # self.CheckParamInt("Pad", '*'+self.n_pads_per_col_key)
        self.CheckParamBool("Pad", '*' + self.pad_oval_key)
        self.CheckParamBool("Pad", '*' + self.pad_smd_key)
        self.CheckParamBool("Paddle", '*' + self.paddle_enable_key)
        self.CheckParamBool("Misc", '*' + self.land_dim_key)
        self.CheckParamBool("Misc", '*' + self.add_index_key)

    def BuildThisFootprint(self):

        self.draw = XessFpWizardDrawingAids(self.module)

        misc = self.parameters["Misc"]
        pads = self.parameters["Pad"]
        pckg = self.parameters["Package"]
        paddle = self.parameters["Paddle"]

        # Footprints can be specified using land patterns or the IC mechanical dimensions.
        land_dim = misc['*' + self.land_dim_key]
        outline = misc['*' + self.outline_key] / 100.0
        bevel = misc['*' + self.bevel_key] / 100.0
        add_index = misc['*' + self.add_index_key]

        pad_pitch = pads[self.pad_pitch_key]
        pad_width = pads[self.pad_width_key]
        pad_length = pads[self.pad_length_key]
        pad_extension = pads[self.pad_extension_key]
        pad_soldermask_margin = pads[self.pad_soldermask_margin_key]
        pad_paste_fill = pads['*' + self.pad_paste_fill_key] / 100.0
        pad_shape = pcbnew.PAD_OVAL if pads['*' + self.pad_oval_key] else pcbnew.PAD_RECT
        pad_smd = pads['*' + self.pad_smd_key]
        pad_drill = pads[self.pad_drill_key]

        n_pads_per_row = int(pckg['*' + self.n_pads_per_row_key])
        n_pads_per_col = int(pckg['*' + self.n_pads_per_col_key])
        # IC epoxy package dimensions.
        body_width = pckg[self.body_width_key]
        body_height = pckg[self.body_height_key]
        # Mechanical dimensions from side-to-side pin-tip to pin-tip.
        total_width = pckg[self.total_width_key]
        total_height = pckg[self.total_height_key]
        if pad_smd is False:
            # For through-hole pins, the pins go through the center of the pad.
            # So add the pad length to the pin tip-to-tip distance to get the
            # pad tip-to-tip distance.
            total_width += pad_length
            total_height += pad_length
        # Land pattern dimensions.
        col_to_col_pitch = pckg[self.col_to_col_pitch_key]
        row_to_row_pitch = pckg[self.row_to_row_pitch_key]
        
        paddle_enable = paddle['*' + self.paddle_enable_key]
        paddle_width = paddle[self.paddle_width_key]
        paddle_height = paddle[self.paddle_height_key]
        paddle_orgx = paddle[self.paddle_orgx_key]
        paddle_orgy = paddle[self.paddle_orgy_key]
        paddle_soldermask_margin = paddle[self.paddle_soldermask_margin_key]
        paddle_paste_fill = paddle['*' + self.paddle_paste_fill_key] / 100.0

        if land_dim: # For footprint land dimensions.
            pitch_adjustment = 0
            row_to_row_pitch += pitch_adjustment
            col_to_col_pitch += pitch_adjustment
        else: # For footprint mechanical dimensions.
            pitch_adjustment = - pad_length
            row_to_row_pitch = total_height + pitch_adjustment
            col_to_col_pitch = total_width + pitch_adjustment

        if pad_smd is True:
            h_pad = PA.PadMaker(self.module).SMDPad(pad_width, pad_length + pad_extension, shape=pad_shape)
            v_pad = PA.PadMaker(self.module).SMDPad(pad_length + pad_extension, pad_width, shape=pad_shape)
        else:
            h_pad = PA.PadMaker(self.module).THPad(pad_width, pad_length + pad_extension, pad_drill, shape=pad_shape)
            v_pad = PA.PadMaker(self.module).THPad(pad_length + pad_extension, pad_width, pad_drill, shape=pad_shape)
        h_pad.SetLocalSolderMaskMargin(pad_soldermask_margin)
        v_pad.SetLocalSolderMaskMargin(pad_soldermask_margin)
        m = calc_solderpaste_margin(pad_width, pad_length + pad_extension, pad_paste_fill)
        h_pad.SetLocalSolderPasteMargin(m)
        v_pad.SetLocalSolderPasteMargin(m)

        # left column
        if n_pads_per_col != 0:
            pin1Pos = pcbnew.wxPoint(-col_to_col_pitch / 2.0, 0)
            offset = pcbnew.wxPoint(-pad_extension/2.0, 0)
            h_pad.SetOffset(offset)
            array = PA.PadLineArray(h_pad, n_pads_per_col, pad_pitch, True, pin1Pos)
            array.SetFirstPadInArray(1)
            array.AddPadsToModule(self.draw)

        # bottom row
        if n_pads_per_row != 0:
            pin1Pos = pcbnew.wxPoint(0, row_to_row_pitch / 2.0)
            offset = pcbnew.wxPoint(0, pad_extension/2.0)
            v_pad.SetOffset(offset)
            array = PA.PadLineArray(v_pad, n_pads_per_row, pad_pitch, False, pin1Pos)
            array.SetFirstPadInArray(n_pads_per_col + 1)
            array.AddPadsToModule(self.draw)

        # right column
        if n_pads_per_col != 0:
            pin1Pos = pcbnew.wxPoint(col_to_col_pitch / 2.0, 0)
            offset = pcbnew.wxPoint(pad_extension/2.0, 0)
            h_pad.SetOffset(offset)
            array = PA.PadLineArray(h_pad, n_pads_per_col, -pad_pitch, True, pin1Pos)
            array.SetFirstPadInArray(n_pads_per_col + n_pads_per_row + 1)
            array.AddPadsToModule(self.draw)

        # top row
        if n_pads_per_row != 0:
            pin1Pos = pcbnew.wxPoint(0, -row_to_row_pitch / 2.0)
            offset = pcbnew.wxPoint(0, -pad_extension/2.0)
            v_pad.SetOffset(offset)
            array = PA.PadLineArray(v_pad, n_pads_per_row, -pad_pitch, False, pin1Pos)
            array.SetFirstPadInArray(2 * n_pads_per_col + n_pads_per_row + 1)
            array.AddPadsToModule(self.draw)
            
        # Thermal paddle.
        if paddle_enable is True:
            t_pad = PA.PadMaker(self.module).SMDPad(paddle_width, paddle_height, shape=pcbnew.PAD_RECT)
            t_pad_pos = pcbnew.wxPoint(paddle_orgx, paddle_orgy)
            t_pad.SetLocalSolderMaskMargin(paddle_soldermask_margin)
            m = calc_solderpaste_margin(paddle_width, paddle_height, paddle_paste_fill)
            t_pad.SetLocalSolderPasteMargin(m)
            array = PA.PadLineArray(t_pad, 1, 0, False, t_pad_pos)
            array.SetFirstPadInArray(2*(n_pads_per_col+n_pads_per_row)+1)
            array.AddPadsToModule(self.draw)

        if n_pads_per_row == 0:
            row_to_row_pitch = body_height - pad_length - pad_extension
            outline_height = body_height
        else:
            outline_height = row_to_row_pitch - pad_length + 2 * (pad_length + pad_extension) * outline
        if n_pads_per_col == 0:
            outline_width = body_width
        else:
            outline_width = col_to_col_pitch - pad_length + 2 * (pad_length + pad_extension) * outline

        # Silkscreen outline
        h = outline_height / 2.0
        w = outline_width / 2.0
        b = min(outline_height * bevel, outline_width * bevel)
        self.draw.Polyline([(-w, -h + b), (-w, h), (w, h), (w, -h),
                            (-w + b, -h), (-w, -h + b)])
                            
        # Add corner index.
        if add_index is True:
            offset = pad_pitch
            self.draw.Circle(-w-offset, -h-offset, pad_pitch/2.0, filled=True)

        # reference and value
        h1 = (row_to_row_pitch + pad_length + pad_extension) / 2.0
        h = max(h, h1)
        
        text_size = pcbnew.FromMM(1.2)  # IPC nominal

        text_offset = h + text_size + pad_pitch/2.0

        self.draw.Value(0, -text_offset, text_size)
        self.draw.Reference(0, text_offset, text_size)

            
class XessBgaPckgWizard(XessFpWizard):

    def GetName(self):
        return "Area-Pin Chips"

    def GetDescription(self):
        return "Ball Grid Arrays"

    n_pads_per_col_key = '#Rows (Vertical)'
    n_pads_per_row_key = '#Cols (Horizontal)'
    total_width_key = 'Width (D)'
    total_height_key = 'Height (E)'
    pad_pitch_key = 'Pitch (e)'
    pad_width_key = 'Size (b)'
    pad_soldermask_margin_key = 'Soldermask Margin'
    pad_paste_fill_key = 'Paste Fill (%)'
    fp_name_key = 'Footprint Name'
    fp_ref_key = 'Reference Prefix'
    outline_key = 'Silkscreen Outline (%)'
    bevel_key = 'Bevel (%)'
    add_index_key = 'Add index (Y/N)'

    def GenerateParameterList(self):
        self.AddParam("Package", self.n_pads_per_row_key, self.uNatural, 16)
        self.AddParam("Package", self.n_pads_per_col_key, self.uNatural, 16)
        self.AddParam("Package", self.total_width_key, self.uMM, 14)
        self.AddParam("Package", self.total_height_key, self.uMM, 14)
        self.AddParam("Pad", self.pad_pitch_key, self.uMM, 0.8)
        self.AddParam("Pad", self.pad_width_key, self.uMM, 0.45)
        self.AddParam("Pad", self.pad_soldermask_margin_key, self.uMM, 0)
        self.AddParam("Pad", self.pad_paste_fill_key, self.uNatural, 100)
        self.AddParam("Misc", self.fp_name_key, self.uString, 'Footprint Name')
        self.AddParam("Misc", self.fp_ref_key, self.uString, 'U')
        self.AddParam("Misc", self.outline_key, self.uNatural, 100)
        self.AddParam("Misc", self.bevel_key, self.uNatural, 7)
        self.AddParam("Misc", self.add_index_key, self.uBool, False)

    def CheckParameters(self):

        # self.CheckParamInt("Pad", '*'+self.n_pads_per_row_key)
        # self.CheckParamInt("Pad", '*'+self.n_pads_per_col_key)
        self.CheckParamBool("Misc", '*' + self.add_index_key)

    def BuildThisFootprint(self):

        self.draw = XessFpWizardDrawingAids(self.module)

        pads = self.parameters["Pad"]
        pckg = self.parameters["Package"]
        misc = self.parameters["Misc"]

        n_pads_per_row = int(pckg['*' + self.n_pads_per_row_key])
        n_pads_per_col = int(pckg['*' + self.n_pads_per_col_key])
        total_width = pckg[self.total_width_key]
        total_height = pckg[self.total_height_key]

        pad_pitch = pads[self.pad_pitch_key]
        pad_width = pads[self.pad_width_key]
        pad_soldermask_margin = pads[self.pad_soldermask_margin_key]
        pad_paste_fill = pads['*' + self.pad_paste_fill_key] / 100.0
        pad_length = pad_width
        pad_shape = pcbnew.PAD_CIRCLE

        outline = misc['*' + self.outline_key] / 100.0
        bevel = misc['*' + self.bevel_key] / 100.0
        add_index = misc['*' + self.add_index_key]

        pad = PA.PadMaker(self.module).SMDPad(pad_width, pad_length, shape=pad_shape)
        pad.SetLayerSet(pad.SMDMask())
        pad.SetLocalSolderMaskMargin(pad_soldermask_margin)
        m = int(floor(pad_width * (1.0 - sqrt(pad_paste_fill))))
        pad.SetLocalSolderPasteMargin(m)

        class BGAPadGridArray(PA.PadGridArray):

            def NamingFunction(self, n_x, n_y):
                return "%s%d" % (
                    self.AlphaNameFromNumber(n_y + 1, alphabet="ABCDEFGHJKLMNPRTUVWY"),
                    n_x + 1)
                    
        # Draw pads.
        array = BGAPadGridArray(pad, n_pads_per_col, n_pads_per_row, pad_pitch, pad_pitch)
        array.AddPadsToModule(self.draw)

        # Draw outline.
        h = total_height / 2.0 * outline
        w = total_width / 2.0 * outline
        b = min(total_height * bevel, total_width * bevel)
        self.draw.Polyline([(-w, -h + b), (-w, h), (w, h), (w, -h),
                            (-w + b, -h), (-w, -h + b)])
                            
        # Add corner index.
        if add_index is True:
            offset = pad_pitch
            self.draw.Circle(-w-offset, -h-offset, pad_pitch/2.0, filled=True)

        # Add reference and value.
        text_size = pcbnew.FromMM(1.2)  # IPC nominal

        text_offset = h + text_size + pad_pitch / 2.0

        self.draw.Value(0, -text_offset, text_size)
        self.draw.Reference(0, text_offset, text_size)
        
        
XessPeriphPckgWizard().register()
XessBgaPckgWizard().register()
