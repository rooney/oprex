
# parsetab.py
# This file is automatically generated. Do not edit.
_tabversion = '3.2'

_lr_method = 'LALR'

_lr_signature = 'N[\x85f\x0c9c\xdd=\x83\x1b\x96\xa8\x0cZ\xcd'
    
_lr_action_items = {'DEDENT':([9,10,21,22,25,29,30,33,39,40,41,42,],[15,-6,-18,-20,33,-19,-21,-7,-22,-23,-25,-24,]),'QUESTMARK':([11,20,28,],[18,27,35,]),'INDENT':([3,10,],[4,17,]),'WHITESPACE':([0,],[2,]),'VARNAME':([3,4,7,10,14,16,17,19,21,22,23,30,32,33,39,40,41,42,],[5,5,11,-6,20,24,-17,11,24,-20,24,-21,37,-7,-22,-23,-25,-24,]),'NEWLINE':([0,5,6,12,19,26,36,37,38,],[3,-8,10,-9,-10,-11,41,-8,42,]),'GLOBALMARK':([10,16,17,21,22,30,33,39,40,41,42,],[-6,23,-17,23,-20,-21,-7,-22,-23,-25,-24,]),'LITERAL':([32,],[38,]),'COLON':([24,37,],[31,31,]),'CHARCLASS':([31,],[36,]),'SLASH':([3,4,11,13,18,28,32,34,35,],[7,7,-12,19,-13,-14,7,-16,-15,]),'LPAREN':([7,19,],[14,14,]),'RPAREN':([20,27,],[28,34,]),'EQUALSIGN':([24,37,],[32,32,]),'$end':([0,1,2,3,8,10,15,33,],[-1,0,-2,-3,-4,-6,-5,-7,]),}

_lr_action = { }
for _k, _v in _lr_action_items.items():
   for _x,_y in zip(_v[0],_v[1]):
      if not _x in _lr_action:  _lr_action[_x] = { }
      _lr_action[_x][_k] = _y
del _lr_action_items

_lr_goto_items = {'definition':([16,21,],[21,21,]),'oprex':([0,],[1,]),'assignment':([16,21,23,32,],[22,22,30,39,]),'cells':([7,19,],[12,26,]),'cell':([7,19,],[13,13,]),'beginscope':([10,],[16,]),'lookup':([3,4,32,],[6,6,6,]),'definitions':([16,21,],[25,29,]),'expression':([3,4,32,],[8,9,40,]),}

_lr_goto = { }
for _k, _v in _lr_goto_items.items():
   for _x,_y in zip(_v[0],_v[1]):
       if not _x in _lr_goto: _lr_goto[_x] = { }
       _lr_goto[_x][_k] = _y
del _lr_goto_items
_lr_productions = [
  ("S' -> oprex","S'",1,None,None,None),
  ('oprex -> <empty>','oprex',0,'p_oprex','/home/ron/oprex/oprex.py',210),
  ('oprex -> WHITESPACE','oprex',1,'p_oprex','/home/ron/oprex/oprex.py',211),
  ('oprex -> NEWLINE','oprex',1,'p_oprex','/home/ron/oprex/oprex.py',212),
  ('oprex -> NEWLINE expression','oprex',2,'p_oprex','/home/ron/oprex/oprex.py',213),
  ('oprex -> NEWLINE INDENT expression DEDENT','oprex',4,'p_oprex','/home/ron/oprex/oprex.py',214),
  ('expression -> lookup NEWLINE','expression',2,'p_expression','/home/ron/oprex/oprex.py',225),
  ('expression -> lookup NEWLINE beginscope definitions DEDENT','expression',5,'p_expression','/home/ron/oprex/oprex.py',226),
  ('lookup -> VARNAME','lookup',1,'p_lookup','/home/ron/oprex/oprex.py',248),
  ('lookup -> SLASH cells','lookup',2,'p_lookup','/home/ron/oprex/oprex.py',249),
  ('cells -> cell SLASH','cells',2,'p_cells','/home/ron/oprex/oprex.py',260),
  ('cells -> cell SLASH cells','cells',3,'p_cells','/home/ron/oprex/oprex.py',261),
  ('cell -> VARNAME','cell',1,'p_cell','/home/ron/oprex/oprex.py',271),
  ('cell -> VARNAME QUESTMARK','cell',2,'p_cell','/home/ron/oprex/oprex.py',272),
  ('cell -> LPAREN VARNAME RPAREN','cell',3,'p_cell','/home/ron/oprex/oprex.py',273),
  ('cell -> LPAREN VARNAME RPAREN QUESTMARK','cell',4,'p_cell','/home/ron/oprex/oprex.py',274),
  ('cell -> LPAREN VARNAME QUESTMARK RPAREN','cell',4,'p_cell','/home/ron/oprex/oprex.py',275),
  ('beginscope -> INDENT','beginscope',1,'p_beginscope','/home/ron/oprex/oprex.py',306),
  ('definitions -> definition','definitions',1,'p_definitions','/home/ron/oprex/oprex.py',312),
  ('definitions -> definition definitions','definitions',2,'p_definitions','/home/ron/oprex/oprex.py',313),
  ('definition -> assignment','definition',1,'p_definition','/home/ron/oprex/oprex.py',322),
  ('definition -> GLOBALMARK assignment','definition',2,'p_definition','/home/ron/oprex/oprex.py',323),
  ('assignment -> VARNAME EQUALSIGN assignment','assignment',3,'p_assignment','/home/ron/oprex/oprex.py',350),
  ('assignment -> VARNAME EQUALSIGN expression','assignment',3,'p_assignment','/home/ron/oprex/oprex.py',351),
  ('assignment -> VARNAME EQUALSIGN LITERAL NEWLINE','assignment',4,'p_assignment','/home/ron/oprex/oprex.py',352),
  ('assignment -> VARNAME COLON CHARCLASS NEWLINE','assignment',4,'p_assignment','/home/ron/oprex/oprex.py',353),
]
