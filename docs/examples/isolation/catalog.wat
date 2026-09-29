(module
  (func (export "price") (param $quantity i32) (result i32)
    local.get $quantity
    i32.const 125
    i32.mul))
