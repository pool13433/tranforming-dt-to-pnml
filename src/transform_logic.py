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

from data_converter import *
from config_manager import *

reload(sys)
sys.setdefaultencoding('utf-8')
today = date.today()
dailydate = today.strftime("%Y%m%d")
'''logging.basicConfig(filename='./logs/transform_' + dailydate + '.log', level=logging.DEBUG,
				format='%(asctime)s - %(levelname)s - %(message)s')'''


class TransformationLogic():

	def __init__(self,root_path):
		self.assign_configs(root_path=root_path)

		self.pnml_options = {'y_space': 90, 'x_space' : 40,'break_space' : 90}
		self.arcs = {'CT': [], 'D': [], 'R': [], 'RT': [], 'DT': [] , 'BREAK' : []}
		# append key from config
		# 'A' : [],'C' : [],
		self.arcs[self._ACTION] = []
		self.arcs[self._CONDITION] = []

	def get_location(self):				
		return {
			'D': {'x': str(self.cal_location_space(1)), 'y': '125'},
			'DT': {'x': str(self.cal_location_space(2)), 'y': '125'},
			'C': {'x': str(self.cal_location_space(3)), 'y': '140'},
			'X' : {'x': str(self.cal_location_space(4)), 'y': '140'},
			'CT': {'x': str(self.cal_location_space(5)), 'y': '50'},
			'R': {'x': str(self.cal_location_space(6)), 'y': '50'},
			'RT': {'x': str(self.cal_location_space(7)), 'y': '50'},			
			'A': {'x': str(self.cal_location_space(8)), 'y': '140'},			
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

	def grep_char(self, str):
		chars = re.findall('[a-zA-Z]+', str)
		if len(chars) > 0:
			return chars[0], len(chars)
		return '', 0

	def push_arcs(self, arc_key, arc_dict):
		# print('arc_key ::=='+json.dumps(arc_key))
		# print('arc_dict ::=='+json.dumps(arc_dict))
		arc_group, arc_len = self.grep_char(arc_key)
		numbers = re.findall('\d+', arc_key.replace('.', ''))
		sub_numbers = re.findall('\d+', arc_key)
		# print('numbers ::=='+json.dumps(numbers))
		if arc_len > 0:
			arc_index = numbers[0]
			# print('arc_index ::=='+arc_index)
			# print('arc_group ::=='+json.dumps(arc_group,indent=2, sort_keys=True))
			if arc_group in self.arcs:
				# print('arc_index ::=='+str(arc_index))
				# print('arc_key ::=='+str(arc_key)+'\n')
				if 'index' not in arc_dict:
					arc_dict['index'] = int(arc_index)
				self.arcs[arc_group].append(arc_dict)

	def draw_place(self, page, place_dict):
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

		# print('uuid ::=='+uuid+' name_text::=='+name_text+'\n')
		arc_data = {'id': uuid}
		if 'index' in _name:
			arc_data['index'] = _name['index']
		if 'unique' in place_dict:
			arc_data['unique'] = place_dict['unique']
		self.push_arcs(name_text, arc_data)

	def cal_location_space(self,seq):
		x_firt = 35
		x_distance = 105
		x_space = self.pnml_options['x_space']
		return (x_space*seq) + ((x_distance*seq) + x_firt)

	def draw_places(self, page, store):
		# rows = get_decision_rows()

		place_offset = self.get_location()
		# Place Group "A*"
		place_index = 1
		for a_idx in sorted(store['ACTION']):
			key = a_idx
			values = store['ACTION'][a_idx]
			# print('values ::=='+json.dumps(values))
			# c_desc = values['Variable/Description']
			c_desc = store['V_JOINS'][key]
			place_text = a_idx
			place_offset, place_index = self.draw_place_ac(page, key, place_offset, c_desc, place_index)

		# Place Group "C*"
		place_index = 1
		for c_idx in sorted(store['CONDITION']):
			key = c_idx
			values = store['CONDITION'][c_idx]
			# c_desc = values['Variable/Description']
			c_desc = store['V_JOINS'][key]
			place_text = c_idx
			offset_y = place_offset['C']['y']
			place_offset, place_index = self.draw_place_ac(page, key, place_offset, c_desc, place_index)

			# xor condition 20191101
			if c_idx in store['XOR_EXTEND']:				
				print('c_idx::=='+str(c_idx))
				key = store['XOR_EXTEND'][c_idx]+key
				place_offset['X']['y'] = offset_y
				place_offset, place_index = self.draw_place_ac(page, key, place_offset, c_desc, place_index)

		# Place Group D* , R*
		place_index = {'R': 1, 'D': 1}
		store_rc = store['RULE']['CONDITION']
		for r_idx in sorted(store_rc):
			r_values = store_rc[r_idx]
			# print('r_values::=='+str(r_values))
			key = r_idx
			# child D
			place_offset, place_index = self.draw_place_d(page, key, place_offset, place_index)
			# print('r_idx::=='+str(r_idx))
			dashs = self.find_dash(r_values)
			# print('len_dashs::=='+str(dashs))
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

	def draw_place_ac(self, page, key, place_offset, place_text, place_index):
		value_dict = {
			'name': {'text': key, 'id': 'ac-3BB8-AC2', 'offset': {'x': '0', 'y': '-10'}},
			'label': {'text': place_text, 'offset': {'x': '10', 'y': '-10'}},
			'graphics': {'offset': {}}
		}
		graphics = value_dict['graphics']
		
		if str(key).startswith(self._BREAK):
			offset_a = place_offset[self._BREAK]
			graphics['offset'] = offset_a
			offset_a['x'] = str(int(offset_a['x']) - self.pnml_options['break_space'])
			offset_a['y'] = str(int(offset_a['y'])) # + self.pnml_options['break_space'])
		else:
			if str(key).startswith(self._CONDITION):
				
				offset_c = place_offset['C']
				graphics['offset'] = offset_c
				offset_c['x'] = str(int(offset_c['x']))
				offset_c['y'] = str(int(offset_c['y']) + self.pnml_options['y_space'])

			elif str(key).startswith(self._ACTION):
				offset_a = place_offset['A']
				graphics['offset'] = offset_a
				offset_a['x'] = str(int(offset_a['x']))
				offset_a['y'] = str(int(offset_a['y']) + self.pnml_options['y_space'])
			
			elif str(key).startswith(self._XOR):
				offset_x = place_offset['X']
				offset_c = place_offset['C']
				#offset_x['y'] = offset_c['y'] # position same C
				graphics['offset'] = offset_x
				offset_x['x'] = str(int(offset_x['x']))
				offset_x['y'] = str(int(offset_x['y']) + self.pnml_options['y_space'])

		value_dict['unique'] = key
		self.draw_place(page, value_dict)
		return place_offset, place_index

	def draw_transition(self, page, transition_dict):
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

			arc_data = {'id': name_id}
			if 'unique' in transition_dict:
				arc_data['unique'] = transition_dict['unique']
			if 'unique_ext' in transition_dict:
				arc_data['unique_ext'] = transition_dict['unique_ext']
			self.push_arcs(name_text, arc_data)

		if 'graphics' in transition_dict:
			graphics_offset = transition_dict['graphics']['offset']

			# child1
			graphics = SubElement(transition, 'graphics')
			position = SubElement(graphics, 'position', graphics_offset)

	def draw_transitions(self, page, store):
		# columns = get_decision_columns()
		# rows = get_decision_rows()
		tran_index = {'CT': 1, 'DT': 1, 'RT': 1}
		tran_offset = self.get_location()

		store_rc = store['RULE']['CONDITION']
		# print('store_rc::=='+json.dumps(store_rc))
		for r_key in sorted(store_rc):
			r_values = store_rc[r_key]
			rc_idx = store_rc.keys().index(r_key)
			# print('rc_idx::=='+str(rc_idx))
			# print('r_key::=='+str(r_key))
			# print('r_values::=='+str(r_values))
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
					# print('ct_key ::=='+ct_key)
					tran_offset, tran_index = self.draw_transition_ctrt(page, ctrt_data, tran_offset, tran_index)
					# child0 [RT]
					ctrt_data['dash_key'] = trans_keys['RT'] + '.' + str(couter_float + 1)
					# print('rt_key ::=='+rt_key)
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
		key_char, key_len = self.grep_char(key)
		# print('key ::=='+str(key))
		# print('key_char ::=='+str(key_char))
		# print('trans_offset ::=='+json.dumps(trans_offset))
		# print('trans_idx ::=='+json.dumps(trans_idx))
		# return
		if key_len > 0:
			idx = trans_idx[key_char]
			# print('trans_idx::=='+str(idx))
			offset = trans_offset[key_char]
			trans_id = key_char + self.concat_unique(offset) + '-' + str(idx) + str(key_char)
			trans_text = key_char + str(idx)

			# raw arc_data push to arcs collection
			arc_data = {
				'name': {'text': trans_text, 'id': trans_id, 'offset': {'x': '0', 'y': '0'}},
				'graphics': {'offset': offset},
				'unique': key
			}
			if 'unique' in ctrt_data:
				arc_data['unique'] = ctrt_data['unique']
			if 'unique_ext' in ctrt_data:
				arc_data['unique_ext'] = ctrt_data['unique_ext']  # 'unique_ext'
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
			# print('source::='+json.dumps(source))
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
		# print('draw_DT_C::=='+json.dumps(self.arcs))
		c_dicts = self.arcs[target_key]
		# print('\nstore_rc'+json.dumps(store_rc,indent=1))
		# print('\nc_dicts::=='+json.dumps(c_dicts))
		# print('len_store_rc'+json.dumps(store_rc,indent=1))
		# print('len_self.arcs[source_key]'+json.dumps(self.arcs[source_key],indent=1))
		for source in self.arcs[source_key]:
			# print('source::=='+json.dumps(source))
			dt_idx = source['index']
			dt_id = source['id']
			dt_unique = source['unique']
			# print('dt_unique::=='+json.dumps(dt_unique))
			# print('store_rc::=='+json.dumps(store_rc))
			r_dict = store_rc[dt_unique]

			for c_key in r_dict:
				# c_value = c_dict[c_key]
				c_dict = self.find_one(c_dicts, 'unique', c_key)
				if c_dict is not None:
					# print('c_dict::=='+json.dumps(c_dict))
					c_id = c_dict['id']
					c_idx = c_dict['index']
					c_unique = c_dict['unique']
					# print('c_key::=='+json.dumps(c_key))
					# print('c_value::=='+json.dumps(c_value))
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
		# print('\nstore_ra'+json.dumps(store_ra))
		# print('\na_dicts::=='+json.dumps(a_dicts))
		# print('\nrt_dicts::=='+json.dumps(rt_dicts))
		# for r_key in sorted(store_ra):
		for r_dict in rt_dicts:
			r_key = r_dict['unique']
			rt_id = r_dict['id']
			# print('r_key::=='+str(r_key))
			c_values = store_ra[r_key]
			# print('c_values::=='+json.dumps(c_values))
			for c_key in c_values:
				# print('c_key::=='+json.dumps(c_key))
				a_dict = self.find_one(a_dicts, 'unique', c_key)
				if a_dict is not None:
					a_id = a_dict['id']
					a_key = a_dict['unique']
					# print('a_dict::=='+json.dumps(a_dict))
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
		store_RCR_EXT = store['RCR_EXTEND']
		# print("store_RCR_EXT::=="+json.dumps(store_RCR_EXT))
		# print('c_dicts::=='+json.dumps(c_dicts))
		# print('ct_dicts::=='+json.dumps(ct_dicts))

		for c_key in sorted(store_RCR_EXT):
			# print('c_key::=='+json.dumps(c_key))
			c_values = store_RCR_EXT[c_key]
			# print('r_values::=='+json.dumps(r_values))
			arcC_dicts = filter(lambda _dict: _dict['unique'] == c_key, c_dicts)
			if len(arcC_dicts) > 0:
				c_dict = arcC_dicts[0]
				c_id = c_dict['id']
				for r_key in c_values:
					# print('r_key::=='+json.dumps(r_key))
					r_vals = c_values[r_key]
					for ext_dict in r_vals:
						# print('ext_dict::=='+json.dumps(ext_dict))
						ext_key, ext_val = ext_dict.items()[0]
						# print('ext_key::=='+str(ext_key)+' ext_val::=='+str(ext_val))
						arcCT_dicts = filter(lambda _dict: _dict['unique_ext'] == ext_key, ct_dicts)
						if len(arcCT_dicts) > 0:
							for ct_dict in arcCT_dicts:
								# print('ct_dict::=='+json.dumps(ct_dict))
								ct_id = ct_dict['id']
								ct_key = ct_dict['id']
								arc_data = {
									'c_key': c_key, 'ext_key': ext_key,
									'id': c_key + '-' + ct_key + c_id + '-' + ct_id,
									'source': c_id, 'target': ct_id
								}
								# print('arc_data::=='+json.dumps(arc_data))
								if 'F' == ext_val:
									arc_data['type'] = 'inhibitor'
								self.draw_arc(page, arc_data)

	def find_name(self, ext_dict, ext_key):
		ext_val = filter(lambda _dict: _dict['name'] == ext_key, ext_dict)
		if len(ext_val) > 0:
			return ext_val[0]
		else:
			return None

	def find_one(self, c_dict, source_key, equal_key):
		# return find(lambda _key: c_dict[_key] == equal_key,c_dict)
		# print('c_dict::=='+json.dumps(c_dict))
		# print('equal_key::=='+json.dumps(equal_key))
		c_unique = filter(lambda item: item[source_key] == equal_key, c_dict)
		# print('c_unique::=='+json.dumps(c_unique))
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
			# print('arc_idx::=='+json.dumps((arc_idx)))
			source = arc_idx.get("source")
			target = arc_idx.get("target")
			childs = arc_idx.getchildren()
			if target not in target_dict:
				target_dict[target] = {'all': 0, 'child': 0}

			target_dict[target]['all'] += 1
			if len(childs) > 0:
				# print('childs ::==' + childs[0].tag)
				target_dict[target]['child'] += 1
				# print('name::==' + str(source))
		# print('target_dict::=='+json.dumps(target_dict,indent=1))

		# +++++++++++ check key [all & child] equaly ++++++++++++++++
		inhibitors = {}
		if len(target_dict) > 0:
			for target in target_dict:
				target_val = target_dict[target]
				# print('target::=='+str(target))
				# print('target_val::=='+json.dumps(target_val))
				len_all = target_val['all']
				len_child = target_val['child']
				if len_all == len_child:
					print('draw_arc extend')
					offset = self.find_offset(page=page, tag_id=target)
					inhibitors[target] = {
						'target' : target,'offset': offset , 
						'text' : offset['text']}
		return inhibitors

	def find_offset(self, page, tag_id):
		transitions = page.findall('transition')
		for plc_idx in transitions:
			_id = plc_idx.get('id')
			# print('tag_id::=='+str(tag_id))
			# print('_id::=='+str(_id))
			if tag_id == _id:
				tag_graphics = plc_idx.find('graphics')
				tag_position = tag_graphics.find('position')
				tag_name = plc_idx.find('name')
				_text = tag_name.find('text').text
				_grap_x = tag_position.get('x')
				_grap_y = tag_position.get('y')
				# print('_position attrs'+json.dumps(_position.attrib))				
				tag_dict = copy.deepcopy(tag_position.attrib)
				tag_dict['text'] = _text				
				return tag_dict
		return {}


	def draw_inhibitor(self, page):
		alias_key = self._BREAK
		inhibitors = self.find_inhibitor(page=page)
		#print('inhibitors::==' + json.dumps(inhibitors))
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
				place_offset, place_index = self.draw_place_ac(page, key, place_offset, 
												'', place_index)
				# draw condition break line
				break_list = self.arcs[alias_key]
				if len(break_list) > 0:
					break_dict = break_list[0]
					#print('break_dict::=='+json.dumps(break_dict))
					place_id = break_dict['id']
					break_lines = {
						'forward' : {'source' : inh_idx , 'target' : place_id},
						'turnback' : {'source' : place_id , 'target' : inh_idx},					
					}
					for line_key in break_lines:
						_break = break_lines[line_key]
						source_key = _break['source']
						source_id = _break['source']
						target_key = _break['target']
						target_id = _break['target']
						self.draw_arc(page, {
							'id': source_key + '-' + target_key + source_id + '-' + target_id,
							'source': source_id,
							'target': target_id
						})
		else:
			print('not ')

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
