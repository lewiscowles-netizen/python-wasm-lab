(module
  (import "left" "read" (func $left-read (param i32) (result i32)))
  (import "left" "write" (func $left-write (param i32 i32)))
  (import "right" "read" (func $right-read (param i32) (result i32)))
  (func (export "observe") (result i32 i32)
    i32.const 0
    i32.const 77
    call $left-write
    i32.const 0
    call $left-read
    i32.const 0
    call $right-read))
