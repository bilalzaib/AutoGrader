from a01 import code_holder 

def test_third():
    assert code_holder(15, 39) == 54

def test_array():
    v1 = [1, 2, 3] 
    v2 = [2, 3, 4] 

    for i in range(0, len(v1)): 
        v1x = v1[i] 
        v2x = v2[i] 
        assert code_holder(v1x, v2x) == v1x + v2x  
