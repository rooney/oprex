
# parsetab.py
# This file is automatically generated. Do not edit.
_tabversion = '3.2'

_lr_method = 'LALR'

_lr_signature = '\xe9\xe1R\xeb4\xd6#a\r\xffR\\.Zu\xb4'
    
_lr_action_items = {'DEDENT':([8,11,17,18,21,23,24,25,27,28,29,32,33,34,],[12,-6,-14,-8,-14,27,-14,-15,-7,33,-16,-17,-9,-18,]),'INDENT':([3,11,18,],[4,17,24,]),'WHITESPACE':([0,],[2,]),'NEWLINE':([0,6,9,13,14,16,19,20,30,31,],[3,11,-12,18,-12,-10,-13,-11,34,11,]),'QUESTION':([10,],[15,]),'EQUALS':([22,31,],[26,26,]),'LITERAL':([26,],[30,]),'SLASH':([3,4,10,15,26,],[5,5,16,20,5,]),'VARIABLE':([3,4,5,9,11,14,16,17,18,20,21,24,26,27,29,32,33,34,],[6,6,10,10,-6,10,-10,22,-8,-11,22,22,31,-7,-16,-17,-9,-18,]),'$end':([0,1,2,3,7,11,12,18,27,33,],[-1,0,-2,-3,-4,-6,-5,-8,-7,-9,]),}

_lr_action = { }
for _k, _v in _lr_action_items.items():
   for _x,_y in zip(_v[0],_v[1]):
      if not _x in _lr_action:  _lr_action[_x] = { }
      _lr_action[_x][_k] = _y
del _lr_action_items

_lr_goto_items = {'definition':([17,21,24,26,],[21,21,21,29,]),'oprex':([0,],[1,]),'cell':([5,9,14,],[9,14,14,]),'moreCells':([9,14,],[13,19,]),'definitions':([17,21,24,],[23,25,28,]),'expression':([3,4,26,],[7,8,32,]),}

_lr_goto = { }
for _k, _v in _lr_goto_items.items():
   for _x,_y in zip(_v[0],_v[1]):
       if not _x in _lr_goto: _lr_goto[_x] = { }
       _lr_goto[_x][_k] = _y
del _lr_goto_items
_lr_productions = [
  ("S' -> oprex","S'",1,None,None,None),
  ('oprex -> <empty>','oprex',0,'p_oprex','oprex.py',144),
  ('oprex -> WHITESPACE','oprex',1,'p_oprex','oprex.py',145),
  ('oprex -> NEWLINE','oprex',1,'p_oprex','oprex.py',146),
  ('oprex -> NEWLINE expression','oprex',2,'p_oprex','oprex.py',147),
  ('oprex -> NEWLINE INDENT expression DEDENT','oprex',4,'p_oprex','oprex.py',148),
  ('expression -> VARIABLE NEWLINE','expression',2,'p_expression','oprex.py',158),
  ('expression -> VARIABLE NEWLINE INDENT definitions DEDENT','expression',5,'p_expression','oprex.py',159),
  ('expression -> SLASH cell moreCells NEWLINE','expression',4,'p_expression','oprex.py',160),
  ('expression -> SLASH cell moreCells NEWLINE INDENT definitions DEDENT','expression',7,'p_expression','oprex.py',161),
  ('cell -> VARIABLE SLASH','cell',2,'p_cell','oprex.py',174),
  ('cell -> VARIABLE QUESTION SLASH','cell',3,'p_cell','oprex.py',175),
  ('moreCells -> <empty>','moreCells',0,'p_moreCells','oprex.py',183),
  ('moreCells -> cell moreCells','moreCells',2,'p_moreCells','oprex.py',184),
  ('definitions -> <empty>','definitions',0,'p_definitions','oprex.py',192),
  ('definitions -> definition definitions','definitions',2,'p_definitions','oprex.py',193),
  ('definition -> VARIABLE EQUALS definition','definition',3,'p_definition','oprex.py',197),
  ('definition -> VARIABLE EQUALS expression','definition',3,'p_definition','oprex.py',198),
  ('definition -> VARIABLE EQUALS LITERAL NEWLINE','definition',4,'p_definition','oprex.py',199),
]