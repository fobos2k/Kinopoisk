import struct
import urllib2
import socket
import zlib, re

class QtParser():
    def __init__(self):
        self.url, self.fp, self.info = None, None, {}
        self.video_formats = {'2vuY', 'avc1', 'cvid', 'dvc ', 'dvcp', 'gif ', 'h263', 'jpeg', 'kpcd', 'mjpa', 'mjpb',
                              'mp4v', 'png ', 'raw ', 'rle ', 'rpza', 'smc ', 'SVQ1', 'SVQ3', 'tiff', 'v210', 'v216',
                              'v308', 'v408', 'v410', 'yuv2'}

    def unpack(self, type, data):
        if data:
            if type == 'I' and len(data) < 4:
                data = data.rjust(4, '\x00')
            return struct.unpack('>' + type, data)[0]

    def fread(self, bytes):
        if self.fp:
            return self.fp.read(bytes)
        else:
            return None

    def urlopen(self, obj):
        try:
            return urllib2.urlopen(obj, timeout=10)
        except urllib2.URLError, e:
            Log.Warn("Timeout for open trailer url")
            print 'Timeout'
        except socket.timeout:
            Log.Warn("Timeout for open trailer url")
            print 'Timeout'
        return None


    def openurl(self, link):
        self.url = link
        self.fp = self.urlopen(self.url)
        if self.fp:
            self.info = {}
            self.info['filesize'] = self.fp.info().getheaders("Content-Length")[0]
            self.info['baseoffset'] = 0
            self.info['fileformat'] = 'mp4'
            self.info['video'] = {}
            self.info['audio'] = {}
            self.info['streams'] = []
            return True
        else:
            return False

    def reopen(self, start):
        request = urllib2.Request(self.url)
        request.add_header("range", "bytes=%s-" % start)
        self.fp = self.urlopen(request)

    def check_qt(self, data):
        return re.search('^.{4}(cmov|free|ftyp|mdat|moov|pnot|skip|wide)', data)

    def analyze(self):
        bflag = True
        bchecked = False
        offset = 0
        apendix = None
        while bflag and int(offset) < int(self.info['filesize']):
            atomheader = self.fread(8)
            if not bchecked:
                bchecked = True
                if self.check_qt(atomheader) is None:
                    break

            atomsize = self.unpack('I', atomheader[0:4])
            atomname = atomheader[4:8]

            if atomname[:2] == 'ee':
                print 'correcting size'
                atomname = atomheader[2:6]
                atomsize = self.unpack('I', atomheader[0:2])
                apendix = atomheader[6:8]

            self.info[atomname] = {}
            self.info[atomname]['name'] = atomname
            self.info[atomname]['size'] = atomsize
            self.info[atomname]['offset'] = offset
            if atomname == 'mdat' and atomsize != 8:
                self.info[atomname] = self.parse_atom(atomname, atomsize, None, offset)
                if 'moov' not in self.info:
                    self.reopen(offset+atomsize)
                else:
                    bflag = False

            elif atomsize != 0:
                if apendix:
                    self.info[atomname] = self.parse_atom(atomname, atomsize, apendix+self.fread(atomsize - 8 - len(apendix)), offset)
                    apendix = None
                else:
                    self.info[atomname] = self.parse_atom(atomname, atomsize, self.fread(atomsize - 8), offset)
            offset = offset + atomsize
        if 'moov' in self.info:
            self.info['bitrate'] = ((self.info['avdataend'] - self.info['avdataoffset']) * 8) / self.info[
                'playtime_seconds']
            self.info.pop('moov', None)
            return self.info
        return None

    def parse_atom(self, atomname, atomsize, atomdata, baseoffset):
        atoms = {
            'ftyp': self.parseatom_ftyp
            , 'moov': self.parsecontainer
            , 'cmov': self.parsecontainer
            , 'cmvd': self.parseatom_cmvd
            , 'trak': self.parsecontainer
            , 'tkhd': self.parseatom_tkhd
            , 'mdia': self.parsecontainer
            , 'minf': self.parsecontainer
            , 'stbl': self.parseatom_stbl
            , 'stsd': self.parseatom_stsd
            , 'mvhd': self.parseatom_mvhd
            , 'mdat': self.parseatom_mdat
            , '\x00\x00\x00\x01': self.parseatom_hex
            , '\x00\x00\x00\x02': self.parseatom_hex
            , '\x00\x00\x00\x03': self.parseatom_hex
            , '\x00\x00\x00\x04': self.parseatom_hex
            , '\x00\x00\x00\x05': self.parseatom_hex

        }

        atom_structure = {'name': atomname, 'size': atomsize, 'offset': baseoffset}
        if atomname in atoms:
            atoms[atomname](atom_structure, atomname, atomsize, atomdata, baseoffset)
        return atom_structure

    def parseatom_cmvd(self, atom_structure, atomname, atomsize, atomdata, baseoffset):
        atom_structure['unCompressedSize'] = self.unpack('I', atomdata[0:4])
        self.parsecontainer(atom_structure, atomname, atomsize, zlib.decompress(atomdata[4:]), baseoffset)

    def parseatom_mdat(self, atom_structure, atomname, atomsize, atomdata, baseoffset):
        self.info['mdat'] = {'name': 'mdat', 'offset': baseoffset, 'size': atomsize}
        self.info['avdataoffset'] = baseoffset + 8
        self.info['avdataend'] = self.info['avdataoffset'] + atomsize

    def parseatom_mvhd(self, atom_structure, atomname, atomsize, atomdata, baseoffset):
        atom_structure['time_scale'] = self.unpack('I', atomdata[12:16])
        atom_structure['duration'] = self.unpack('I', atomdata[16:20])
        self.info['playtime_seconds'] = atom_structure['duration'] / (atom_structure['time_scale'] * 1.0)

    def parseatom_hex(self, atom_structure, atomname, atomsize, atomdata, baseoffset):
        atom_structure['name'] = self.unpack('I', atomname)
        self.parsecontainer(atom_structure, atom_structure['name'], atomsize, atomdata, baseoffset)

    def parseatom_stbl(self, atom_structure, atomname, atomsize, atomdata, baseoffset):
        self.parsecontainer(atom_structure, atomname, atomsize, atomdata, baseoffset)
        is_video = False
        for atom in atom_structure['subatoms']:
            if 'sample_description_table' in atom:
                for smtbl in atom['sample_description_table']:
                    if 'data_format' in smtbl:
                        if smtbl['data_format'] in self.video_formats:
                            is_video = True
                            self.info['video']['codec_fourcc'] = smtbl['data_format']

        self.info['streams'].append('video' if is_video else 'audio')

    def parseatom_stsd(self, atom_structure, atomname, atomsize, atomdata, baseoffset):
        atom_structure['version'] = self.unpack('B', atomdata[0:1])
        atom_structure['flags_raw'] = self.unpack('H', atomdata[1:3])
        atom_structure['number_entries'] = self.unpack('I', atomdata[4:8])
        atom_structure['sample_description_table'] = []
        stsddataoffset = 8
        i = 0
        while i < atom_structure['number_entries']:
            smp_tbl = {'size': self.unpack('I', atomdata[
                                                stsddataoffset:stsddataoffset + 4])}
            stsddataoffset = stsddataoffset + 4
            smp_tbl['data_format'] = atomdata[stsddataoffset:stsddataoffset + 4]
            stsddataoffset = stsddataoffset + 10
            smp_tbl['reference_index'] = self.unpack('H', atomdata[
                                                          stsddataoffset:stsddataoffset + 2])
            stsddataoffset = stsddataoffset + 2
            smp_tbl['data'] = atomdata[
                              stsddataoffset:stsddataoffset + smp_tbl['size'] - 16]
            stsddataoffset = stsddataoffset + smp_tbl['size'] - 16

            smp_tbl['encoder_version'] = self.unpack('H', smp_tbl['data'][0:2])
            smp_tbl['encoder_revision'] = self.unpack('H', smp_tbl['data'][2:4])
            smp_tbl['encoder_vendor'] = smp_tbl['data'][4:8]

            if smp_tbl['encoder_vendor'] == '\x00\x00\x00\x00':
                smp_tbl['audio_channels'] = self.unpack('H', smp_tbl['data'][8:10])
                smp_tbl['audio_bit_depth'] = self.unpack('H', smp_tbl['data'][10:12])
                smp_tbl['audio_compression_id'] = self.unpack('H', smp_tbl['data'][12:14])
                smp_tbl['audio_packet_size'] = self.unpack('H', smp_tbl['data'][14:16])
                smp_tbl['audio_sample_rate'] = self.unpack('H', smp_tbl['data'][16:18]) + float(
                    self.unpack('H', smp_tbl['data'][18:20])) / 65535

                smp_tbl['temporal_quality'] = self.unpack('I', smp_tbl['data'][8:12])
                smp_tbl['spatial_quality'] = self.unpack('I', smp_tbl['data'][12:16])
                smp_tbl['width'] = self.unpack('H', smp_tbl['data'][16:18])
                smp_tbl['height'] = self.unpack('H', smp_tbl['data'][18:20])
                smp_tbl['resolution_x'] = self.unpack('H', smp_tbl['data'][24:26]) + float(
                    self.unpack('H', smp_tbl['data'][26:28])) / 65535
                smp_tbl['resolution_y'] = self.unpack('H', smp_tbl['data'][28:30]) + float(
                    self.unpack('H', smp_tbl['data'][30:32])) / 65535
                smp_tbl['data_size'] = self.unpack('I', smp_tbl['data'][32:36])
                smp_tbl['frame_count'] = self.unpack('H', smp_tbl['data'][36:38])
                smp_tbl['compressor_name'] = smp_tbl['data'][38:42]
                smp_tbl['pixel_depth'] = self.unpack('H', smp_tbl['data'][42:44])
                smp_tbl['color_table_id'] = self.unpack('H', smp_tbl['data'][44:46])

                if smp_tbl['data_format'] in self.video_formats:
                    self.info['fileformat'] = 'mp4'
                    self.info['video']['fourcc'] = smp_tbl['data_format']
                    if smp_tbl['width'] and smp_tbl['height']:
                        self.info['video']['resolution_x'] = smp_tbl['width']
                        self.info['video']['resolution_y'] = smp_tbl['height']
                elif smp_tbl['data_format'] == 'qtvr':
                    self.info['video']['dataformat'] = 'quicktimevr'
                else:
                    self.info['audio']['codec'] = smp_tbl['data_format']
                    self.info['audio']['sample_rate'] = smp_tbl['audio_sample_rate']
                    self.info['audio']['channels'] = smp_tbl['audio_channels']
                    self.info['audio']['bit_depth'] = smp_tbl['audio_bit_depth']
            else:
                if smp_tbl['data_format'] == 'mp4s':
                    self.info['fileformat'] = 'mp4'
                else:
                    smp_tbl['video_temporal_quality'] = self.unpack('I', smp_tbl['data'][8:12])
                    smp_tbl['video_spatial_quality'] = self.unpack('I', smp_tbl['data'][12:16])
                    smp_tbl['video_frame_width'] = self.unpack('H', smp_tbl['data'][16:18])
                    smp_tbl['video_frame_height'] = self.unpack('H', smp_tbl['data'][18:20])
                    smp_tbl['video_resolution_x'] = self.unpack('H', smp_tbl['data'][20:22]) + float(
                        self.unpack('H', smp_tbl['data'][22:24])) / 65535
                    smp_tbl['video_resolution_y'] = self.unpack('H', smp_tbl['data'][24:26]) + float(
                        self.unpack('H', smp_tbl['data'][26:28])) / 65535
                    smp_tbl['video_data_size'] = self.unpack('I', smp_tbl['data'][28:32])
                    smp_tbl['video_frame_count'] = self.unpack('H', smp_tbl['data'][32:34])
                    smp_tbl['video_encoder_name_len'] = self.unpack('B', smp_tbl['data'][34:35])
                    smp_tbl['video_encoder_name'] = smp_tbl['data'][35:35 + smp_tbl['video_encoder_name_len']]
                    smp_tbl['video_pixel_color_depth'] = self.unpack('H', smp_tbl['data'][66:68])
                    smp_tbl['video_color_table_id'] = self.unpack('H', smp_tbl['data'][68:70])
                    smp_tbl['video_pixel_color_type'] = 'gray' if smp_tbl['video_pixel_color_depth'] > 32 else 'color'
                    smp_tbl['video_pixel_color_name'] = self.colornamelookup(smp_tbl['video_pixel_color_depth'])

                    if smp_tbl['video_pixel_color_name'] != 'invalid':
                        self.info['video']['codec'] = smp_tbl['data_format']
                        self.info['video']['bits_per_sample'] = smp_tbl['video_pixel_color_depth']

                if smp_tbl['data_format'] == 'mp4a':
                    self.info['audio']['dataformat'] = 'mp4'
                elif smp_tbl['data_format'] in {'3ivx', '3iv1', '3iv2'}:
                    self.info['video']['dataformat'] = '3ivx'
                elif smp_tbl['data_format'] == 'xvid':
                    self.info['video']['dataformat'] = 'xvid'
                elif smp_tbl['data_format'] == 'mp4v':
                    self.info['video']['dataformat'] = 'mpeg4'
                elif smp_tbl['data_format'] in {'divx', 'div1', 'div2', 'div3', 'div4', 'div5', 'div6'}:
                    self.info['video']['dataformat'] = 'divx'

            smp_tbl.pop('data', None)
            atom_structure['sample_description_table'].append(smp_tbl)
            i = i + 1

    def parseatom_ftyp(self, atom_structure, atomname, atomsize, atomdata, baseoffset):
        atom_structure['signature'] = atomdata[0:4]
        atom_structure['unknown_1'] = self.unpack('I', atomdata[4:8])
        atom_structure['fourcc'] = atomdata[8:12]

    def parseatom_tkhd(self, atom_structure, atomname, atomsize, atomdata, baseoffset):
        atom_structure['version'] = self.unpack('B', atomdata[0:1])
        atom_structure['flags_raw'] = self.unpack('I', '\x00' + atomdata[1:4])
        atom_structure['creation_time'] = self.unpack('I', atomdata[4:8])
        atom_structure['modify_time'] = self.unpack('I', atomdata[8:12])
        atom_structure['trackid'] = self.unpack('I', atomdata[12:16])
        atom_structure['reserved1'] = self.unpack('I', atomdata[16:20])
        atom_structure['duration'] = self.unpack('I', atomdata[20:24])
        atom_structure['reserved2'] = self.unpack('Q', atomdata[24:32])
        atom_structure['layer'] = self.unpack('H', atomdata[32:34])
        atom_structure['alternate_group'] = self.unpack('H', atomdata[34:36])
        atom_structure['volume'] = self.unpack('H', atomdata[36:38])
        atom_structure['reserved3'] = self.unpack('H', atomdata[38:40])
        atom_structure['width'] = self.unpack('h', atomdata[76:78]) + float(self.unpack('H', atomdata[78:80])) / 65535
        atom_structure['height'] = self.unpack('h', atomdata[80:82]) + float(self.unpack('H', atomdata[82:84])) / 65535
        atom_structure['flags'] = {}
        atom_structure['flags']['enabled'] = bool(atom_structure['flags_raw'] & 0x0001)
        atom_structure['flags']['in_movie'] = bool(atom_structure['flags_raw'] & 0x0002)
        atom_structure['flags']['in_preview'] = bool(atom_structure['flags_raw'] & 0x0004)
        atom_structure['flags']['in_poster'] = bool(atom_structure['flags_raw'] & 0x0008)

        if atom_structure['flags']['enabled'] == 1:
            if 'resolution_x' not in self.info['video'] or 'resolution_y' not in self.info['video']:
                self.info['video']['resolution_x'] = int(atom_structure['width'])
                self.info['video']['resolution_y'] = int(atom_structure['height'])

            self.info['video']['resolution_x'] = max(self.info['video']['resolution_x'], int(atom_structure['width']))
            self.info['video']['resolution_y'] = max(self.info['video']['resolution_y'], int(atom_structure['height']))

    def parsecontainer(self, atom_structure, atomname, atomsize, atomdata, baseoffset):
        baseoffset = baseoffset + 8
        atom_structure['subatoms'] = []
        subatomoffset = 0
        subatomcnt = 0
        while subatomoffset < len(atomdata):
            subatomsize = self.unpack('I', atomdata[subatomoffset:subatomoffset + 4])
            subatomname = atomdata[subatomoffset + 4:subatomoffset + 8]
            subatomdata = atomdata[subatomoffset + 8:subatomoffset + subatomsize]
            atom_structure['subatoms'].append(self.parse_atom(subatomname, subatomsize, subatomdata,
                                                              baseoffset + subatomoffset))
            subatomcnt = subatomcnt + 1
            subatomoffset = subatomoffset + subatomsize

    def colornamelookup(self, colorid):
        colors = {
            1: '2-color (monochrome)'
            , 2: '4-color'
            , 4: '16-color'
            , 8: '256-color'
            , 16: 'thousands (16-bit color)'
            , 24: 'millions (24-bit color)'
            , 32: 'millions+ (32-bit color)'
            , 33: 'black & white'
            , 34: '4-gray'
            , 36: '16-gray'
            , 40: '256-gray'
        }
        return colors[colorid] if colorid in colors else 'invalid'