import pytest, re
import syllabare as syl


### BASIC TESTS OF FUNCTIONALITY ###

def test_findall_hiragana():
    syl.set_map('maps/hiragana.json')
    # Find all symbols containing the 'O' sound
    res = syl.findall(r'O', 'いろはにほへと')
    assert res == ['ろ', 'ほ', 'と']

def test_findall_cherokee():
    syl.set_map('maps/cherokee.json')
    # Find all symbols containing the `I` sound
    res = syl.findall(r"I", "Ꭲ Ꮳ Ꮅ Ꮝ Ꭰ Ꮑ Ꮧ")
    assert res == ['Ꭲ', 'Ꮅ', 'Ꮧ']

def test_findall_cherokee_with_I_flag():
    syl.set_map('maps/cherokee.json')
    # Find all symbols containing the `I` sound
    res = syl.findall(r"i", "Ꭲ Ꮳ Ꮅ Ꮝ Ꭰ Ꮑ Ꮧ")
    assert res == None
    res = syl.findall(r"i", "Ꭲ Ꮳ Ꮅ Ꮝ Ꭰ Ꮑ Ꮧ", syl.I)
    assert res == ['Ꭲ', 'Ꮅ', 'Ꮧ']

def test_sub_hiragana():
    syl.set_map('maps/hiragana.json')
    # Replace the 'O' sound with 'A'
    res = syl.sub(r'O', r'A', 'いろはにほへと')
    assert res == 'いらはにはへた'

def test_sub_ipa():
    syl.set_map('maps/ipa.json')
    # Substitute voiceless (vl) sounds with their voiced (vd) counterparts
    res = syl.sub(r'vl', r'vd', 'tɛstɪŋ')
    assert res == 'dɛzdɪŋ'
    # Change the place of articulation
    res = syl.sub(r'alveolar', r'velar', 'tɛstɪŋ')
    assert res == 'kɛxkɪŋ'
