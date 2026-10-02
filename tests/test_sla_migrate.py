import copy
import pathlib
import sys
import unittest

sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'tools'))
from sla_migrate import MigrationError, SlaSlice, decision_pairs, instruction_pattern, merge_pattern, shape


def node(ident,attrs=(),children=()):
    return {'id':ident,'attrs':[{'id':i,'type':t,'value':v} for i,t,v in attrs],'children':list(children)}


def pattern(mask,value):
    return node(18,children=[node(7,[(6,'signed-positive',0),(10,'signed-positive',1)],
                                 [node(6,[(8,'unsigned',mask<<24),(2,'unsigned',value<<24)])])])


def leaf(pairs):
    return node(16,[(20,'signed-positive',len(pairs)),(21,'boolean',False),(14,'signed-positive',0),(15,'signed-positive',0)],
                [node(9,[(3,'signed-positive',ident)],[pattern(mask,value)]) for ident,mask,value in pairs])


def selector_fixture():
    p=SlaSlice.__new__(SlaSlice)
    p.big=False
    p.heads={20:('selector',0,77)}
    p.registers={i+4:{'name':f'G{i}','space':'register','offset':i*8,'size_bytes':8} for i in range(3)}
    token=node(27,[(35,'boolean',False),(31,'boolean',False),(14,'signed-positive',10),(30,'signed-positive',11),
                   (33,'signed-positive',1),(32,'signed-positive',1),(29,'signed-positive',2)])
    p.bodies={20:node(76,[(3,'unsigned',20)],[token,*[node(28,[(3,'unsigned',i+4)]) for i in range(3)],node(11)])}
    return p


class SlaMigrationTest(unittest.TestCase):
    def test_pattern_words_are_instruction_byte_streams(self):
        self.assertEqual(instruction_pattern(pattern(0xf7,7)),(0xf7,7))
        self.assertEqual(merge_pattern((0xf7,7),(8,8)),(255,15))
        with self.assertRaises(MigrationError): merge_pattern((255,15),(8,0))
        malformed=pattern(255,15)
        malformed['children'][0]['attrs'][1]['value']=5
        with self.assertRaises(MigrationError): instruction_pattern(malformed)
        malformed=pattern(255,15)
        malformed['children'][0]['children'][0]['attrs'][0]['value']=0
        with self.assertRaises(MigrationError): instruction_pattern(malformed)

    def test_decision_constraints_and_leaf_order_are_preserved(self):
        tree=node(16,[(20,'signed-positive',3),(21,'boolean',False),(14,'signed-positive',0),(15,'signed-positive',1)],
                  [leaf([(4,255,0x42),(91,0x7f,0x42)]),leaf([(5,255,0xc2)])])
        self.assertEqual(list(decision_pairs(tree)),[(4,(255,0x42)),(91,(255,0x42)),(5,(255,0xc2))])
        tree['attrs'][1]['value']=True
        with self.assertRaises(MigrationError): list(decision_pairs(tree))
        tree['attrs'][1]['value']=False
        tree['children'].pop()
        with self.assertRaises(MigrationError): list(decision_pairs(tree))

    def test_selector_holes_and_identity_mapping_are_derived(self):
        p=selector_fixture()
        f=p.field(20)
        self.assertEqual((f['offset'],f['bits'],f['exclude']),(10,2,[3]))
        self.assertEqual([v['name'] for v in f['registers']],['G0','G1','G2'])
        for mutation in ['nonidentity','wrong_width','signed','big','unknown','bad_extent']:
            q=copy.deepcopy(p)
            if mutation=='nonidentity': q.registers[5]['offset']=16
            elif mutation=='wrong_width': q.registers[5]['size_bytes']=4
            elif mutation=='signed': q.bodies[20]['children'][0]['attrs'][1]['value']=True
            elif mutation=='big': q.big=True
            elif mutation=='unknown': q.bodies[20]['children'][1]['attrs'][0]['value']=99
            else: q.bodies[20]['children'].pop()
            with self.subTest(mutation=mutation),self.assertRaises((MigrationError,KeyError)): q.field(20)

    def test_unknown_attributes_types_and_dynamic_handles_refuse(self):
        hand=node(2,children=[node(4,[(2,'signed-positive',1),(5,'signed-positive',i)]) for i in range(3)])
        self.assertEqual(SlaSlice.handle(hand),1)
        hand['children'][1]['attrs'][1]['value']=3
        with self.assertRaises(MigrationError): SlaSlice.handle(hand)
        n=node(1,[(2,'unsigned',0),(99,'unsigned',0)])
        with self.assertRaises(MigrationError): shape(n,1,{2:'unsigned'})
        n=node(1,[(2,'unsigned',0),(2,'unsigned',0)])
        with self.assertRaises(MigrationError): shape(n,1,{2:'unsigned'})
        n=node(1,[(2,'string','0')])
        with self.assertRaises(MigrationError): shape(n,1,{2:'unsigned'})


if __name__=='__main__': unittest.main()
