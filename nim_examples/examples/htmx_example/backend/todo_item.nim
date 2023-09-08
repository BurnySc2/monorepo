import mustache, tables
import sequtils

type
    TodoItem* = tuple
        id: int
        text: string
        done: bool

# https://github.com/soasme/nim-mustache/blob/274d13260485594b81e7fd74e7c93125c76ed1d4/tests/test_values.nim#L62
proc castValue*(value: TodoItem): Value =
    let newValue = new(Table[string, Value])
    result = Value(kind: vkTable, vTable: newValue)
    for k, v in value.fieldPairs:
        newValue[k] = v.castValue

proc castValue*(value: seq[TodoItem]): Value =
    Value(kind: vkSeq, vSeq: value.mapIt(it.castValue))

