"""运行 python3 check_hello.py 验证；练习只修改 hello.py。"""
from hello import normalize_username


if __name__ == "__main__":
    assert normalize_username(" alice ") == "alice", "应去除两端空格"
    assert normalize_username("\tbob\n") == "bob", "应去除制表符和换行"
    assert normalize_username("Mary Jane") == "Mary Jane", "应保留名字中间的空格"
    assert normalize_username("") == "", "应支持空字符串"
    print("PASS: 4 cases")
