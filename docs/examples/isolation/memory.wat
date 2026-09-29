(module
  (memory (export "memory") 1 2)
  (data (i32.const 0) "\2a\2b")
  (func (export "read") (param $offset i32) (result i32)
    local.get $offset
    i32.load8_u)
  (func (export "write") (param $offset i32) (param $value i32)
    local.get $offset
    local.get $value
    i32.store8)
  (func (export "overwrite-neighbour") (result i32)
    i32.const 1
    i32.const 99
    i32.store8
    i32.const 1
    i32.load8_u)
  (func (export "grow") (result i32)
    i32.const 1
    memory.grow)
  (func (export "spin")
    (loop $again
      br $again)))
