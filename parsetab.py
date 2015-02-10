
# parsetab.py
# This file is automatically generated. Do not edit.
_tabversion = '3.2'

_lr_method = 'LALR'

_lr_signature = '\x15\xa6_\x8d\x83\xb9I\tTX\xa7\xe5\xc7\xf1d\xb3'
    
_lr_action_items = {'QUESTMARK':([10,20,30,],[16,29,38,]),'ENDSCOPE':([8,9,14,15,22,25,27,32,35,36,41,44,45,48,49,50,],[13,-6,-10,-18,-18,35,-8,-19,-7,-18,-20,-21,50,-23,-22,-9,]),'BEGINSCOPE':([2,9,27,],[4,14,14,]),'WHITESPACE':([0,],[1,]),'VARNAME':([2,4,6,9,11,12,14,15,17,19,21,22,26,27,34,35,36,39,41,44,46,47,48,49,50,],[5,5,10,-6,10,20,-10,23,-11,10,31,23,-12,-8,42,-7,23,-13,-20,-21,-15,-14,-23,-22,-9,]),'CLOSEPAREN':([20,29,],[30,37,]),'NEWLINE':([0,5,11,17,18,19,26,28,39,40,42,43,46,47,],[2,9,-16,-11,27,-16,-12,-17,-13,48,9,49,-15,-14,]),'GLOBALMARK':([9,14,15,22,27,34,35,36,41,44,48,49,50,],[-6,-10,21,21,-8,21,-7,21,-20,-21,-23,-22,-9,]),'LITERAL':([34,],[43,]),'COLON':([23,24,31,42,],[-24,33,-25,-24,]),'CHARCLASS':([33,],[40,]),'SLASH':([2,4,10,16,30,34,37,38,],[6,6,17,26,39,6,46,47,]),'EQUALSIGN':([23,24,31,42,],[-24,34,-25,-24,]),'OPENPAREN':([6,11,17,19,26,39,46,47,],[12,12,-11,12,-12,-13,-15,-14,]),'$end':([0,1,2,3,7,9,13,27,35,50,],[-1,-2,-3,0,-4,-6,-5,-8,-7,-9,]),}

_lr_action = { }
for _k, _v in _lr_action_items.items():
   for _x,_y in zip(_v[0],_v[1]):
      if not _x in _lr_action:  _lr_action[_x] = { }
      _lr_action[_x][_k] = _y
del _lr_action_items

_lr_goto_items = {'definition':([15,22,34,36,],[22,22,41,22,]),'oprex':([0,],[3,]),'moreCells':([11,19,],[18,28,]),'vardecl':([15,22,34,36,],[24,24,24,24,]),'cell':([6,11,19,],[11,19,19,]),'beginscope':([9,27,],[15,36,]),'definitions':([15,22,36,],[25,32,45,]),'expression':([2,4,34,],[7,8,44,]),}

_lr_goto = { }
for _k, _v in _lr_goto_items.items():
   for _x,_y in zip(_v[0],_v[1]):
       if not _x in _lr_goto: _lr_goto[_x] = { }
       _lr_goto[_x][_k] = _y
del _lr_goto_items
_lr_productions = [
  ("S' -> oprex","S'",1,None,None,None),
  ('oprex -> <empty>','oprex',0,'p_oprex','oprex.py',201),
  ('oprex -> WHITESPACE','oprex',1,'p_oprex','oprex.py',202),
  ('oprex -> NEWLINE','oprex',1,'p_oprex','oprex.py',203),
  ('oprex -> NEWLINE expression','oprex',2,'p_oprex','oprex.py',204),
  ('oprex -> NEWLINE BEGINSCOPE expression ENDSCOPE','oprex',4,'p_oprex','oprex.py',205),
  ('expression -> VARNAME NEWLINE','expression',2,'p_expression','oprex.py',215),
  ('expression -> VARNAME NEWLINE beginscope definitions ENDSCOPE','expression',5,'p_expression','oprex.py',216),
  ('expression -> SLASH cell moreCells NEWLINE','expression',4,'p_expression','oprex.py',217),
  ('expression -> SLASH cell moreCells NEWLINE beginscope definitions ENDSCOPE','expression',7,'p_expression','oprex.py',218),
  ('beginscope -> BEGINSCOPE','beginscope',1,'p_beginscope','oprex.py',251),
  ('cell -> VARNAME SLASH','cell',2,'p_cell','oprex.py',257),
  ('cell -> VARNAME QUESTMARK SLASH','cell',3,'p_cell','oprex.py',258),
  ('cell -> OPENPAREN VARNAME CLOSEPAREN SLASH','cell',4,'p_cell','oprex.py',259),
  ('cell -> OPENPAREN VARNAME CLOSEPAREN QUESTMARK SLASH','cell',5,'p_cell','oprex.py',260),
  ('cell -> OPENPAREN VARNAME QUESTMARK CLOSEPAREN SLASH','cell',5,'p_cell','oprex.py',261),
  ('moreCells -> <empty>','moreCells',0,'p_moreCells','oprex.py',286),
  ('moreCells -> cell moreCells','moreCells',2,'p_moreCells','oprex.py',287),
  ('definitions -> <empty>','definitions',0,'p_definitions','oprex.py',300),
  ('definitions -> definition definitions','definitions',2,'p_definitions','oprex.py',301),
  ('definition -> vardecl EQUALSIGN definition','definition',3,'p_definition','oprex.py',312),
  ('definition -> vardecl EQUALSIGN expression','definition',3,'p_definition','oprex.py',313),
  ('definition -> vardecl EQUALSIGN LITERAL NEWLINE','definition',4,'p_definition','oprex.py',314),
  ('definition -> vardecl COLON CHARCLASS NEWLINE','definition',4,'p_definition','oprex.py',315),
  ('vardecl -> VARNAME','vardecl',1,'p_vardecl','oprex.py',345),
  ('vardecl -> GLOBALMARK VARNAME','vardecl',2,'p_vardecl','oprex.py',346),
]
