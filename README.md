# Invoice-gen
### TODO
```python 
    def calculatae(total_cgst,total_sgst):
        total_tax = total_cgst + total_sgst
        return total_tax
```

pip3 install num2words
pip3 install bson.json_util

#### make a direcorty
static/pdf_stored

as this is empty directory git won't add

change the dirctory of file stored at app.py if you want

#### what needs to calculated in client side ?
* sno

* HSN Code

* product_desc

* discount_percentage

* taxable_value 
    * Which is taxable_value = unit_price * quantity
    * taxable_value does not include any discounted value as its calculated at serverside
    * you can show users preview of calculated values but don't send ??

* CGST

* SGST

#### What are calculated at server side ?

* Total amount before TAX added

* Dicount amount from percentage given

* SGST & CGST amount from percentage from JSON

* Total Amount of CGST & SGST

* Total amount of TAX = CGST + SGST

* Total amount after TAX
