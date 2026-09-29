(module
  (import "catalog" "price" (func $price (param i32) (result i32)))
  (func (export "quote") (param $quantity i32) (result i32)
    local.get $quantity
    call $price))
