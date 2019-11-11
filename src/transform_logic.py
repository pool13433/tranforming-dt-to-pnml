import pandas as pd
import logging
import json
import sys
import re
import collections
import copy

from datetime import date
from xml.etree.ElementTree import Element, SubElement, tostring, XML
from xml.dom import minidom
from collections import OrderedDict
from inspect import currentframe

from data_converter import *
from config_manager import *

reload(sys)
sys.setdefaultencoding('utf-8')
today = date.today()
dailydate = today.strftime("%Y%m%d")
'''logging.basicConfig(filename='./logs/transform_' + dailydate + '.log', level=logging.DEBUG,
				format='%(asctime)s - %(levelname)s - %(message)s')'''

def debug_print(arg):
    frameinfo = currentframe()
    print(frameinfo.f_back.f_lineno,arg)	

class TransformationLogic():

	def __init__(self,root_path):
		config = self.assign_configs(root_path=root_path)

		self.arcs = {'CT': [], 'D': [], 'R': [], 'RT': [], 'DT': [] , 
					'BREAK' : [],'XOR' : [], 'T' : []}
		#inhibitor
		# append key from config
		# 'A' : [],'C' : [],
		self.arcs[self._ACTION] = []
		self.arcs[self._CONDITION] = []

		# set space distance in config
		distance = config['DISTANCE']['VALUES']
		position = config['POSITION']['VALUES']
		#self.pnml_options = {'y_space': 90, 'x_space' : 40,'break_space' : 90}
		self.pnml_options = {}
		self.pnml_options['y_space'] = distance['Y']
		self.pnml_options['x_space'] = distance['X']
		self.pnml_options['break_space'] = distance['BREAK']

		self.pnml_options['rule_place'] = position['RULE']
		self.pnml_options['conact_place'] = position['CONACT']
		self.pnml_options['rule_dash_place'] = position['RULE_DASH']


	def get_location(self):		
		y_place = self.pnml_options	
		y_rule = str(y_place['rule_place'])
		y_conact = str(y_place['conact_place'])
		y_dash = str(y_place['rule_dash_place'])
		return {
			'D': {'x': str(self.cal_location_space(1)), 'y': y_rule},
			'DT': {'x': str(self.cal_location_space(2)), 'y': y_rule},
			'C': {'x': str(self.cal_location_space(3)), 'y': y_conact},
			'T' : {'x': str(self.cal_location_space(4)), 'y': y_conact},
			'XORP' : {'x': str(self.cal_location_space(5)), 'y': y_conact},
			'CT': {'x': str(self.cal_location_space(6)), 'y': y_dash},
			'R': {'x': str(self.cal_location_space(7)), 'y': y_dash},
			'RT': {'x': str(self.cal_location_space(8)), 'y': y_dash},			
			'A': {'x': str(self.cal_location_space(9)), 'y': y_conact},			
		}

	def assign_configs(self,root_path):
		configManager = ConfigManager(root_path=root_path);
		config = configManager.read_configs(json_filename='input.json')
		self._RULE = config['RULE']['ALIAS']
		self._ACTION = config['ACTION']['ALIAS']
		self._CONDITION = config['CONDITION']['ALIAS']
		self._BREAK = 'BREAK'
		self._XOR = config['COLUMN_XOR']['VALUE']
		self._CONFIG = config
		return config

	def grep_char(self, str):
		chars = re.findall('[a-zA-Z]+', str)
		if len(chars) > 0:
			return chars[0], len(chars)
		return '', 0

	def push_arcs(self, arc_key, arc_dict):
		#debug_print('arc_key ::=='+json.dumps(arc_key))
		#print('\narc_dictarc_dictarc_dict ::=='+json.dumps(arc_dict)+'\n')
		arc_group, arc_len = self.grep_char(arc_key)
		#debug_print('\narc_group::=='+str(arc_group)+' arc_len::=='+str(arc_len)+'\n')
		numbers = re.findall('\d+', arc_key.replace('.', ''))
		sub_numbers = re.findall('\d+', arc_key)
		# debug_print('numbers ::=='+json.dumps(numbers))
		if arc_len > 0:
			arc_index = numbers[0]
			# debug_print('arc_index ::=='+arc_index)
			# debug_print('arc_group ::=='+json.dumps(arc_group,indent=2, sort_keys=True))
			if arc_group in self.arcs:
				# debug_print('arc_index ::=='+str(arc_index))
				# debug_print('arc_key ::=='+str(arc_key)+'\n')
				if 'index' not in arc_dict:
					arc_dict['index'] = int(arc_index)
				#print('\n arc_dict<><>arc_dict ::=='+json.dumps(arc_dict)+'\n')
				self.arcs[arc_group].append(arc_dict)

	def draw_place(self, page, place_dict):
		#debug_print('draw place <place/>')
		_name = place_dict['name']
		name_text = _name['text']
		name_offset = _name['offset']
		name_id = _name['id']
		graphics_offset = place_dict['graphics']['offset']

		uuid = name_id + str(name_text)  # 'p-3BB8-AC2EE-2'  ,p-3BB8-AC2

		place = SubElement(page, 'place', {'id': uuid})
		# child0
		name = SubElement(place, 'name')
		text = SubElement(name, 'text')
		text.text = name_text
		graphics = SubElement(name, 'graphics')
		offset = SubElement(graphics, 'offset', name_offset)

		# child1
		if 'label' in place_dict:
			label_text = place_dict['label']['text']
			label_offset = place_dict['label']['offset']

			label = SubElement(place, 'label')
			text = SubElement(label, 'text')
			text.text = label_text
			graphics = SubElement(label, 'graphics')
			offset = SubElement(graphics, 'offset', label_offset)

		elif 'initialMarking' in place_dict:
			initialMarking_text = place_dict['initialMarking']['text']

			initialMarking = SubElement(place, 'initialMarking')
			text = SubElement(initialMarking, 'text')
			text.text = initialMarking_text

		# child2
		graphics = SubElement(place, 'graphics')
		position = SubElement(graphics, 'position', graphics_offset)

		# debug_print('uuid ::=='+uuid+' name_text::=='+name_text+'\n')
		#arc_data = {'id': uuid}
		arc_data = dict({'id': uuid},**place_dict)
		if 'index' in _name:
			arc_data['index'] = _name['index']
		'''if 'unique' in place_dict:
			arc_data['unique'] = place_dict['unique']
		if 'unique_xor' in place_dict:
			arc_data['unique_xor'] = place_dict['unique_xor']'''
		self.push_arcs(name_text, arc_data)

	def cal_location_space(self,seq):
		x_firt = 35
		x_distance = 105
		x_space = self.pnml_options['x_space']
		return (x_space*seq) + ((x_distance*seq) + x_firt)

	def draw_places(self, page, store):
		# rows = get_decision_rows()
		debug_print('draw places <place/>...')
		place_offset = self.get_location()
		#debug_print('place_offset::=='+json.dumps(place_offset))
		# Place Group "A*"
		place_index = 1
		tran_index = {'T': 0}
		for a_idx in sorted(store['ACTION']):
			key = a_idx
			values = store['ACTION'][a_idx]
			# debug_print('values ::=='+json.dumps(values))
			# c_desc = values['Variable/Description']
			c_desc = store['V_JOINS'][key]
			place_text = a_idx
			place_offset, place_index = self.draw_place_ac(page, key, 
											place_offset=place_offset, 
											place_text=c_desc, 
											place_index=place_index)

		# Place Group "C*"
		place_index = 1
		for c_idx in sorted(store['CONDITION']):
			key = c_idx
			values = store['CONDITION'][c_idx]
			# c_desc = values['Variable/Description']
			c_desc = store['V_JOINS'][key]
			place_text = c_idx
			offset_y = place_offset['C']['y']
			place_offset, place_index = self.draw_place_ac(page, key, 
										place_offset=place_offset, 
										place_text=c_desc, 
										place_index=place_index)

			# xor condition 20191101
			for xor_key in store['XOR_EXTEND']:
				#debug_print('xor_key::=='+xor_key)
				xor_values = store['XOR_EXTEND'][xor_key]
				#print('xor_values::=='+json.dumps(xor_values))
				if len(xor_values) > 1:
					if c_idx in xor_values:
						# xml = <transition/>
						key_new = 'T'
						ctrt_data = {
							'unique': key_new, 'unique_ext': key_new,'dash_key' : key_new,
							'unique_xor' : c_idx, 'xor_group' : xor_values 
						}		
						place_offset['T']['y'] = offset_y
						place_offset, tran_index = self.draw_transition_ctrt(page=page, 
													ctrt_data=ctrt_data, 
													trans_offset=place_offset, 
													trans_idx=tran_index)

						# xml => <place/>			
						key_new = xor_key+key
						place_offset['XORP']['y'] = offset_y
						place_offset, place_index = self.draw_place_ac(page, key_new, 
													place_offset=place_offset, 
													place_text='', 
													place_index=place_index,
													xor_dict={'unique_xor' : key})

		# Place Group D* , R*
		place_index = {'R': 1, 'D': 1}
		store_rc = store['RULE']['CONDITION']
		for r_idx in sorted(store_rc):
			r_values = store_rc[r_idx]
			# debug_print('r_values::=='+str(r_values))
			key = r_idx
			# child D
			place_offset, place_index = self.draw_place_d(page, key, place_offset, place_index)
			# debug_print('r_idx::=='+str(r_idx))
			dashs = self.find_dash(r_values)
			# debug_print('len_dashs::=='+str(dashs))
			len_dashs = len(dashs)
			if len_dashs > 0:
				len_dash_power = pow(2, len_dashs)
				for x in range(len_dash_power):
					place_offset, place_index = self.draw_place_r(page, key + '.' + str(x + 1), place_offset,
														 place_index)
			else:
				place_offset, place_index = self.draw_place_r(page, key, place_offset, place_index)

	def find_dash(self, r_values):
		return map(lambda y: r_values[y], filter(lambda x: r_values[x] == '-', r_values))

	def draw_place_d(self, page, key, place_offset, place_index):
		if str(key).startswith(self._RULE):
			offset_d = place_offset['D']
			d_index = place_index['D']
			name_text = 'D' + str(d_index)
			name_id = 'D-' + self.concat_unique(offset_d)
			self.draw_place(page, {
				'name': {'text': name_text, 'index': d_index, 'id': name_id, 'offset': {'x': '0', 'y': '-10'}},
				'initialMarking': {'text': '1'},
				'graphics': {'offset': offset_d}
			})
			offset_d['x'] = str(int(offset_d['x']))
			offset_d['y'] = str(int(offset_d['y']) + self.pnml_options['y_space'])

			place_index['D'] = place_index['D'] + 1

		return place_offset, place_index

	def draw_place_r(self, page, key, place_offset, place_index):
		if str(key).startswith(self._RULE):
			offset_r = place_offset['R']
			r_index = place_index['R']
			self.draw_place(page, {
				'name': {
					'text': key, 'id': 'R-' + self.concat_unique(offset_r),
					'index': r_index, 'offset': {'x': '0', 'y': '-10'}
				},
				'graphics': {'offset': offset_r}
			})
			offset_r['x'] = str(int(offset_r['x']))
			offset_r['y'] = str(int(offset_r['y']) + self.pnml_options['y_space'])
			place_index['R'] = place_index['R'] + 1

		return place_offset, place_index

	def draw_place_ac(self, page, key, place_offset, place_text, place_index,xor_dict=None):		
		_offset = {}
		if str(key).startswith(self._BREAK):
			offset_a = place_offset[self._BREAK]
			_offset = offset_a.copy()
			_offset['x'] = str(int(_offset['x']) + self.pnml_options['break_space'])
			_offset['y'] = str(int(_offset['y']) + self.pnml_options['break_space'])
		else:
			if str(key).startswith(self._CONDITION):
				
				offset_c = place_offset['C']
				_offset = offset_c.copy()
				offset_c['x'] = str(int(offset_c['x']))
				offset_c['y'] = str(int(offset_c['y']) + self.pnml_options['y_space'])

			elif str(key).startswith(self._ACTION):
				offset_a = place_offset['A']
				_offset = offset_a.copy()
				offset_a['x'] = str(int(offset_a['x']))
				offset_a['y'] = str(int(offset_a['y']) + self.pnml_options['y_space'])
			
			elif str(key).startswith(self._XOR):
				offset_x = place_offset['XORP']				
				#offset_x['y'] = offset_c['y'] # position same C
				_offset = offset_x.copy()
				#offset_x['x'] = str(int(offset_x['x']))
				offset_x['y'] = str(int(offset_x['y']) + self.pnml_options['y_space'])				
					#value_dict['label']['offset']['y'] = '100'
					#'label': {'text': place_text, 'offset': {'x': '10', 'y': '-10'}},
		#debug_print('value_dict[\'label\'][\'offset\'][\'y\'] ::=='+str(value_dict['label']['offset']['y']))

		value_dict = {
			'name': {'text': key, 'id': 'ac-3BB8-AC2', 'offset': {'x': '0', 'y': '-10'}},
			'label': {'text': place_text, 'offset': {'x': '10', 'y': '100'}},
			'graphics': {'offset': _offset},
			'unique' : key
		}
		if xor_dict is not None:					
			value_dict['unique_xor'] = xor_dict['unique_xor']		
		self.draw_place(page, value_dict)
		return place_offset, place_index

	def draw_transition(self, page, transition_dict):
		#debug_print('draw transition <transition/>')
		#print('\ntransition_dict::=='+json.dumps(transition_dict)+'\n\n')
		arc_data = dict({},**transition_dict) # merge dict
		#print('\n\narc_data::=='+json.dumps(arc_data)+'\n\n')
		if 'name' in transition_dict:
			name_text = transition_dict['name']['text']
			name_id = transition_dict['name']['id']
			name_offset = transition_dict['name']['offset']

			# child0
			transition = SubElement(page, 'transition', {'id': name_id})
			name = SubElement(transition, 'name')
			text = SubElement(name, 'text')
			text.text = name_text
			graphics = SubElement(name, 'graphics')
			SubElement(graphics, 'offset', name_offset)
			
			arc_data['id']  = name_id
			
			'''if 'unique' in transition_dict:
				arc_data['unique'] = transition_dict['unique']
			if 'unique_ext' in transition_dict:
				arc_data['unique_ext'] = transition_dict['unique_ext']'''
			
			self.push_arcs(name_text, arc_data)

		if 'graphics' in transition_dict:
			graphics_offset = transition_dict['graphics']['offset']

			# child1
			graphics = SubElement(transition, 'graphics')
			position = SubElement(graphics, 'position', graphics_offset)

	def draw_transitions(self, page, store):
		debug_print('draw transitions <transition/>...')
		# columns = get_decision_columns()
		# rows = get_decision_rows()
		tran_index = {'CT': 1, 'DT': 1, 'RT': 1}
		tran_offset = self.get_location()

		store_rc = store['RULE']['CONDITION']
		# debug_print('store_rc::=='+json.dumps(store_rc))
		for r_key in sorted(store_rc):
			r_values = store_rc[r_key]
			rc_idx = store_rc.keys().index(r_key)
			# debug_print('rc_idx::=='+str(rc_idx))
			# debug_print('r_key::=='+str(r_key))
			# debug_print('r_values::=='+str(r_values))
			dashs = self.find_dash(r_values)
			trans_keys = {'CT': 'CT' + str(rc_idx + 1), 'RT': 'RT' + str(rc_idx + 1)}
			ctrt_data = {'unique': r_key, 'unique_ext': r_key}
			len_dashs = len(dashs)
			if len_dashs > 0:
				couter_float = 1
				len_dash_power = pow(2, len_dashs)
				for dash_idx in range(len_dash_power):
					ctrt_data['unique_ext'] = r_key + '.' + str(dash_idx)
					# child0 [CT]
					ctrt_data['dash_key'] = trans_keys['CT'] + '.' + str(couter_float + 1)
					# debug_print('ct_key ::=='+ct_key)
					tran_offset, tran_index = self.draw_transition_ctrt(page, ctrt_data, tran_offset, tran_index)
					# child0 [RT]
					ctrt_data['dash_key'] = trans_keys['RT'] + '.' + str(couter_float + 1)
					# debug_print('rt_key ::=='+rt_key)
					tran_offset, tran_index = self.draw_transition_ctrt(page, ctrt_data, tran_offset, tran_index)
					couter_float = couter_float + 1
			else:
				ctrt_data['unique_ext'] = r_key + '.0'
				# child [CT]
				ctrt_data['dash_key'] = trans_keys['CT']
				tran_offset, tran_index = self.draw_transition_ctrt(page, ctrt_data, tran_offset, tran_index)
				# child [RT]
				ctrt_data['dash_key'] = trans_keys['RT']
				tran_offset, tran_index = self.draw_transition_ctrt(page, ctrt_data, tran_offset, tran_index)

			# child1 [DT]
			# dt_index = transition_index['dt']
			ctrt_data['dash_key'] = 'DT' + str(tran_index['DT'])
			tran_offset, tran_index = self.draw_transition_ctrt(page, ctrt_data, tran_offset, tran_index)

	def draw_transition_ctrt(self, page, ctrt_data, trans_offset, trans_idx):
		key = ctrt_data['dash_key']
		#debug_print('key ::=='+str(key))
		key_char, key_len = self.grep_char(key)
		# debug_print('key ::=='+str(key))
		#debug_print('key_char ::=='+str(key_char))
		# debug_print('trans_offset ::=='+json.dumps(trans_offset))
		# debug_print('trans_idx ::=='+json.dumps(trans_idx))
		# return
		if key_len > 0:
			idx = trans_idx[key_char]
			# debug_print('trans_idx::=='+str(idx))
			offset = trans_offset[key_char]
			trans_id = key_char + self.concat_unique(offset) + '-' + str(idx) + str(key_char)
			trans_text = key_char + str(idx)

			# raw arc_data push to arcs collection
			arc_data = dict({
				'name': {'text': trans_text, 'id': trans_id, 'offset': {'x': '0', 'y': '0'}},
				'graphics': {'offset': offset},
				'unique': key
			},**ctrt_data)
			'''if 'unique' in ctrt_data:
				arc_data['unique'] = ctrt_data['unique']
			if 'unique_ext' in ctrt_data:
				arc_data['unique_ext'] = ctrt_data['unique_ext']  # 'unique_ext'
			if 'unique_xor' in ctrt_data:
				arc_data['unique_xor'] = ctrt_data['unique_xor']  # 'unique_ext' '''
			#print('\narc_data::=='+json.dumps(arc_data)+'\n')
			self.draw_transition(page, arc_data)

			offset['x'] = str(int(offset['x']))
			offset['y'] = str(int(offset['y']) + self.pnml_options['y_space'])			
			trans_idx[key_char] = trans_idx[key_char] + 1
		return trans_offset, trans_idx

	def draw_arc(self, page, arc):
		if 'target' in arc:
			_arc = SubElement(page, 'arc', {
				'id': arc['id'],
				'source': arc['source'],
				'target': arc['target'],
			})
			if 'type' in arc:
				SubElement(_arc, 'type', {
					'value': arc['type']
				})

	def draw_arcline(self, page, source_key, target_key):
		for source in self.arcs[source_key]:
			# debug_print('source::='+json.dumps(source))
			source_idx = source['index']
			source_id = source['id']
			target_array = self.arcs[target_key]
			target_dict = target_array[source_idx - 1]
			target_id = target_dict['id']
			self.draw_arc(page, {
				'id': source_key + '-' + target_key + source_id + '-' + target_id,
				'source': source_id,
				'target': target_id
			})

	def draw_arclineDT_C(self, page, store):
		# DT => C
		source_key = 'DT'
		target_key = self._CONDITION
		store_rc = store['RULE']['CONDITION']
		# debug_print('draw_DT_C::=='+json.dumps(self.arcs))
		c_dicts = self.arcs[target_key]
		# debug_print('\nstore_rc'+json.dumps(store_rc,indent=1))
		# debug_print('\nc_dicts::=='+json.dumps(c_dicts))
		# debug_print('len_store_rc'+json.dumps(store_rc,indent=1))
		# debug_print('len_self.arcs[source_key]'+json.dumps(self.arcs[source_key],indent=1))
		for source in self.arcs[source_key]:
			# debug_print('source::=='+json.dumps(source))
			dt_idx = source['index']
			dt_id = source['id']
			dt_unique = source['unique']
			# debug_print('dt_unique::=='+json.dumps(dt_unique))
			# debug_print('store_rc::=='+json.dumps(store_rc))
			r_dict = store_rc[dt_unique]

			for c_key in r_dict:
				# c_value = c_dict[c_key]
				c_dict = self.find_one(c_dicts, 'unique', c_key)
				if c_dict is not None:
					# debug_print('c_dict::=='+json.dumps(c_dict))
					c_id = c_dict['id']
					c_idx = c_dict['index']
					c_unique = c_dict['unique']
					# debug_print('c_key::=='+json.dumps(c_key))
					# debug_print('c_value::=='+json.dumps(c_value))
					if 'T' == r_dict[c_unique]:
						self.draw_arc(page, {
							'id': source_key + '-' + target_key + dt_id + '-' + c_id,
							'source': dt_id,
							'target': c_id
						})

	def draw_arclineRT_A(self, page, store):
		# RT => A
		source_key = 'RT'
		target_key = self._ACTION
		rt_dicts = self.arcs[source_key]
		a_dicts = self.arcs[target_key]

		store_ra = store['RULE']['ACTION']
		# debug_print('\nstore_ra'+json.dumps(store_ra))
		# debug_print('\na_dicts::=='+json.dumps(a_dicts))
		# debug_print('\nrt_dicts::=='+json.dumps(rt_dicts))
		# for r_key in sorted(store_ra):
		for r_dict in rt_dicts:
			r_key = r_dict['unique']
			rt_id = r_dict['id']
			# debug_print('r_key::=='+str(r_key))
			c_values = store_ra[r_key]
			# debug_print('c_values::=='+json.dumps(c_values))
			for c_key in c_values:
				# debug_print('c_key::=='+json.dumps(c_key))
				a_dict = self.find_one(a_dicts, 'unique', c_key)
				if a_dict is not None:
					a_id = a_dict['id']
					a_key = a_dict['unique']
					# debug_print('a_dict::=='+json.dumps(a_dict))
					if 'X' == c_values[a_key]:
						self.draw_arc(page, {
							'id': source_key + '-' + target_key + rt_id + '-' + a_id,
							'source': rt_id,
							'target': a_id
						})

	def draw_arclineC_CT(self, page, store):
		source_key = self._CONDITION
		target_key = 'CT'
		c_dicts = self.arcs[source_key]
		ct_dicts = self.arcs[target_key]
		xorp_dicts = self.arcs['XOR']
		xort_dicts = self.arcs['T']
		store_RCR_EXT = store['RCR_EXTEND']
		# debug_print("store_RCR_EXT::=="+json.dumps(store_RCR_EXT))
		#debug_print('xorp_dicts::=='+json.dumps(xorp_dicts))
		#debug_print('xort_dicts::=='+json.dumps(xort_dicts))
		# debug_print('ct_dicts::=='+json.dumps(ct_dicts))
		#debug_print('\nself.arcs::=='+json.dumps(self.arcs)+'\n')		
		for c_key in sorted(store_RCR_EXT):
			c_values = store_RCR_EXT[c_key]
			xor_idx = self.find_unique_idx(xor_dicts=xorp_dicts,xor_key=c_key)	
			#debug_print('xor_idx::=='+json.dumps(xor_idx))								
			c_dict = self.find_one(c_dicts, 'unique', c_key)
			if c_dict is not None:
				c_id = c_dict['id']
				# ************** xor ****************
				if xor_idx is not None:
					#debug_print('draw XOR <place/> && <transition/>')	
					c_id = self.draw_arclineXor(page=page,
												xorp_dict=xorp_dicts[xor_idx],
												xort_dict=xort_dicts[xor_idx],c_id=c_id)
				#debug_print('c_id ::=='+str(c_id))
				for r_key in c_values:
					# debug_print('r_key::=='+json.dumps(r_key))
					r_vals = c_values[r_key]
					for ext_dict in r_vals:
						# debug_print('ext_dict::=='+json.dumps(ext_dict))
						ext_key, ext_val = ext_dict.items()[0]
						# debug_print('ext_key::=='+str(ext_key)+' ext_val::=='+str(ext_val))
						arcCT_dicts = filter(lambda _dict: _dict['unique_ext'] == ext_key, ct_dicts)
						if len(arcCT_dicts) > 0:
							for ct_dict in arcCT_dicts:
								# debug_print('ct_dict::=='+json.dumps(ct_dict))
								ct_id = ct_dict['id']
								ct_key = ct_dict['id']
								arc_data = {
									'c_key': c_key, 'ext_key': ext_key,
									'id': c_key + '-' + ct_key + c_id + '-' + ct_id,
									'source': c_id, 'target': ct_id
								}
								# debug_print('arc_data::=='+json.dumps(arc_data))
								if 'F' == ext_val:
									arc_data['type'] = 'inhibitor'
								self.draw_arc(page, arc_data)

		# draw <place/> diagonal
		#print('xorp_dicts ::=='+json.dumps(xorp_dicts))
		for c_key in sorted(store_RCR_EXT):
			c_dict = self.find_one(c_dicts, 'unique', c_key)
			#debug_print('c_dict::=='+json.dumps(c_dict))
			if c_dict is not None:		
				c_id = c_dict['id']		
				xor_idx = self.find_unique_idx(xor_dicts=xorp_dicts,xor_key=c_key)					
				#debug_print('xor_idx::=='+json.dumps(xor_idx))			
				if xor_idx is not None:
					for xort_idx,_xor in enumerate(xort_dicts):
						# ignore case 
						if xort_idx != xor_idx:
							#debug_print('xort_dicts[xort_idx]::=='+json.dumps(xort_dicts[xort_idx]))
							xor_dict = xort_dicts[xort_idx]	
							#print('\nxor_dict:=='+json.dumps(xor_dict)+'\n')
							arc_dict = xor_dict['arc']		
							xor_group = xor_dict['xor_group']

							# check xor group
							if c_key in xor_group:
								print('xor_group ::=='+json.dumps(xor_group))
								#inhibitor
								#t_source = arc_dict['source']
								t_target = arc_dict['target']
								t_key = arc_dict['c_key']
								arc_data = {
									'c_key': t_key, #'ext_key': ext_key,
									'id': t_key + '-' + t_key + c_id + '-' + t_key+str(xort_idx),
									'source': c_id, 'target': t_target,
									'type' : 'inhibitor'
								}	
								#debug_print('arc_data::=='+json.dumps(arc_data))
								self.draw_arc(page, arc_data)

	def find_unique_idx(self,xor_dicts,xor_key):
		#print('xor_key::=='+str(xor_key))
		for idx,xor in enumerate(xor_dicts):
			#print('xor::'+json.dumps(xor))
			#print('idx::'+json.dumps(idx))
			if xor['unique_xor'] == xor_key:
				return idx
		return None;

	def draw_arclineXor(self,page,xorp_dict,xort_dict,c_id):
		#xor_exist = xor_dicts[xor_idx]		
		#debug_print('xor_exist::=='+json.dumps(xor_exist))
		#debug_print('t_exist::=='+json.dumps(t_exist))
		#print('xorp_dict::=='+json.dumps(xorp_dict))

		# draw arc <arc/> <transition/>
		t_id = xort_dict['id']
		t_key = xort_dict['unique']
		arc_data = {
			'c_key': t_key, #'ext_key': ext_key,
			'id': t_key + '-' + t_key + c_id + '-' + t_key,
			'source': c_id, 'target': t_id
		}
		#print('arc_data::=='+json.dumps(arc_data))
		xort_dict['arc'] = arc_data		
		self.draw_arc(page, arc_data)

		# draw arc <arc/> <place/>
		xor_id = xorp_dict['id']
		xor_key = xorp_dict['unique']
		arc_data = {
			'c_key': xor_key, #'ext_key': ext_key,
			'id': xor_key + '-' + xor_key + t_id + '-' + xor_id,
			'source': t_id, 'target': xor_id
		}
		self.draw_arc(page, arc_data)

		#debug_print('xor => ct')				
		#c_id = xor_id
		return xor_id

	def find_name(self, ext_dict, ext_key):
		ext_val = filter(lambda _dict: _dict['name'] == ext_key, ext_dict)
		if len(ext_val) > 0:
			return ext_val[0]
		else:
			return None

	def find_one(self, c_dict, source_key, equal_key):
		# return find(lambda _key: c_dict[_key] == equal_key,c_dict)
		# debug_print('c_dict::=='+json.dumps(c_dict))
		# debug_print('equal_key::=='+json.dumps(equal_key))
		c_unique = filter(lambda item: item[source_key] == equal_key, c_dict)
		# debug_print('c_unique::=='+json.dumps(c_unique))
		if len(c_unique) > 0:
			return c_unique[0]
		else:
			return None

	def draw_arcs(self, page, store):
		store_rc = store['RULE']['CONDITION']
		store_c = store['CONDITION']

		self.draw_arcline(page, 'D', 'DT')
		self.draw_arcline(page, 'CT', 'R')
		self.draw_arcline(page, 'R', 'RT')
		self.draw_arclineDT_C(page, store)
		self.draw_arclineRT_A(page, store)
		self.draw_arclineC_CT(page, store)

	def concat_unique(self, offet):
		return str(offet['x']) + '-' + str(offet['y'])

	def find_inhibitor(self, page):
		target_dict = {}
		_arcs = page.findall('arc')
		# +++++++++++ cound all & child ++++++++++++++++
		for arc_idx in _arcs:
			# debug_print('arc_idx::=='+json.dumps((arc_idx)))
			source = arc_idx.get("source")
			target = arc_idx.get("target")
			childs = arc_idx.getchildren()
			if target not in target_dict:
				target_dict[target] = {'all': 0, 'child': 0}

			target_dict[target]['all'] += 1
			if len(childs) > 0:
				# debug_print('childs ::==' + childs[0].tag)
				target_dict[target]['child'] += 1
				# debug_print('name::==' + str(source))
		# debug_print('target_dict::=='+json.dumps(target_dict,indent=1))

		# +++++++++++ check key [all & child] equaly ++++++++++++++++
		inhibitors = {}
		if len(target_dict) > 0:
			for target in target_dict:
				target_val = target_dict[target]
				# debug_print('target::=='+str(target))
				# debug_print('target_val::=='+json.dumps(target_val))
				len_all = target_val['all']
				len_child = target_val['child']
				if len_all == len_child:
					debug_print('draw_arc extend')
					offset = self.find_offset(page=page, tag_id=target)
					inhibitors[target] = {
						'target' : target,'offset': offset , 
						'text' : offset['text']}
		return inhibitors

	def find_offset(self, page, tag_id):
		transitions = page.findall('transition')
		for plc_idx in transitions:
			_id = plc_idx.get('id')
			# debug_print('tag_id::=='+str(tag_id))
			# debug_print('_id::=='+str(_id))
			if tag_id == _id:
				tag_graphics = plc_idx.find('graphics')
				tag_position = tag_graphics.find('position')
				tag_name = plc_idx.find('name')
				_text = tag_name.find('text').text
				_grap_x = tag_position.get('x')
				_grap_y = tag_position.get('y')
				# debug_print('_position attrs'+json.dumps(_position.attrib))				
				tag_dict = copy.deepcopy(tag_position.attrib)
				tag_dict['text'] = _text				
				return tag_dict
		return {}


	# break all false condition
	def draw_inhibitor(self, page):
		alias_key = self._BREAK
		inhibitors = self.find_inhibitor(page=page)
		#debug_print('inhibitors::==' + json.dumps(inhibitors))
		if len(inhibitors) > 0:
			place_offset = {alias_key: {'x': '0', 'y': '0'},}
			# Place Group "A*"
			place_index = 1
			for inh_idx in inhibitors:
				# draw condition break object
				ctrt_data = inhibitors[inh_idx]				
				key = alias_key+' '+ctrt_data['text'] #
				place_offset[alias_key] =  ctrt_data['offset']
				place_text = ctrt_data['text']
				place_offset, place_index = self.draw_place_ac(page, key, 
												place_offset=place_offset, 
												place_text='', 
												place_index=place_index)
				# draw condition break line
				break_list = self.arcs[alias_key]
				if len(break_list) > 0:
					break_dict = break_list[0]
					#debug_print('break_dict::=='+json.dumps(break_dict))
					place_id = break_dict['id']
					break_lines = {
						'forward' : {'source' : inh_idx , 'target' : place_id},
						'turnback' : {'source' : place_id , 'target' : inh_idx,'type' : 'inhibitor'},					
					}
					for line_key in break_lines:
						_break = break_lines[line_key]
						source_key = _break['source']
						source_id = _break['source']
						target_key = _break['target']
						target_id = _break['target']
						break_data = {
							'id': source_key + '-' + target_key + source_id + '-' + target_id,
							'source': source_id,
							'target': target_id
						}
						if 'type' in _break:
							break_data['type']  = _break['type']
						self.draw_arc(page, break_data)
		'''else:
			debug_print('not ')'''

	def draw_decision_rawdata(self, excellpath, pnmlpath):
		utility = DataConverter(excellpath)
		store = utility.read_rawdata(req_conf=self._CONFIG)

		pnml = Element('pnml')
		pnml.set('xmlns', 'http://www.pnml.org/version-2009/grammar/pnml')

		net = SubElement(pnml, 'net', {
			'id': 'n-3BB8-AC2DF-0',
			'type': 'http://www.laas.fr/tina/tpn'
		})

		name = SubElement(net, 'name')
		SubElement(name, 'text').text = 'buffer1'

		page = SubElement(net, 'page', {'id': 'g-3BB8-AC2EB-1'})

		self.draw_places(page=page, store=store)
		self.draw_transitions(page=page, store=store)
		self.draw_arcs(page=page, store=store)

		self.draw_inhibitor(page=page)

		xmlstr = minidom.parseString(tostring(pnml)).toprettyxml(
			encoding="UTF-8", indent="    ")
		with open(pnmlpath, "w") as f:  # './tina-result.pnml'
			f.write(xmlstr)


def main():
	path = 'D:/NickWork/tina-transform'
	logic = TransformationLogic(root_path=path)
	logic.draw_decision_rawdata(excellpath=path + '/inputs/TestData1.xlsx',
								pnmlpath=path + '/outputs/xxxxxxx.pnml')

if __name__ == "__main__":
	main()
