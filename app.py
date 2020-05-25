import os
from flask import Flask, render_template, request, json, redirect, make_response
from bson.json_util import dumps
from num2words import num2words
from pymongo import MongoClient
import datetime
import currency
import pdfkit
from os import remove
import urllib
app = Flask(__name__)
client = MongoClient("localhost",27017)
db = client["invoice"]

@app.route('/')
def index():
  return "Helloooo"

@app.route('/sendInvoiceData', methods=['POST'])
def sendInvoiceData():
  request_data = request.get_json()
  #extract the data we are going to use in table
  invoicedatas = request_data["invoice_data"]
  #initalized with global scope as we need them in for loop
  total_amount_before_tax = 0.0
  total_cgst_amount = 0.0
  total_sgst_amount = 0.0
  total_tax_amount = 0.0
  total_amount_after_tax = 0.0
  # gives the amount in words
  server_invoice = []
  for data in invoicedatas:
    amt_before = float(data["taxable_value"])
    #check if any discounts offered
    if float(data["discount_percentage"]) != 0:
      #calculate amount of discount with calculate_gst()
      discount_before_tax = calculate_gst(data["discount_percentage"],amt_before)
      # calculate amount after applying discount
      discount_applied_amount = amt_before - discount_before_tax
      #now calculate cgst and sgst
      cgst_amt = calculate_gst(data["CGST"],amt_before)
      sgst_amt = calculate_gst(data["SGST"],amt_before)
      total_amount_sale_line_item = (discount_applied_amount + cgst_amt + sgst_amt)
      total_amount_after_tax += total_amount_sale_line_item
      total_amount_before_tax += amt_before
      total_cgst_amount += cgst_amt
      total_sgst_amount += sgst_amt
      total_tax_amount += cgst_amt + sgst_amt
      #adding everything we caluclated to dict array
      updated_json = data
      currency_code = request_data["currency_code"]
      formatted_total_before_tax = currency.pretty(amt_before,currency_code,trim=True).replace((currency.symbol(currency_code)),(currency.symbol(currency_code)) + " ")
      formatted_cgst_amount = currency.pretty(cgst_amt,currency_code,trim=True).replace((currency.symbol(currency_code)),(currency.symbol(currency_code)) + " ")
      formatted_sgst_amount = currency.pretty(sgst_amt,currency_code,trim=True).replace((currency.symbol(currency_code)),(currency.symbol(currency_code)) + " ")
      formatted_total_amount_sale_line_item = currency.pretty(total_amount_sale_line_item,currency_code,trim=True).replace((currency.symbol(currency_code)),(currency.symbol(currency_code)) + " ")
      formatted_discount_amount = currency.pretty(discount_before_tax,currency_code,trim=True).replace((currency.symbol(currency_code)),(currency.symbol(currency_code)) + " ")
      updated_json.update({"cgst_amt":formatted_cgst_amount,"sgst_amt":formatted_sgst_amount,"formatted_total_before_tax":formatted_total_before_tax,"formatted_discount_amount":formatted_discount_amount,"formatted_total_amount_sale_line_item":formatted_total_amount_sale_line_item})
      server_invoice.append(updated_json)

    else:
      #now calculate cgst and sgst for non discounted
      cgst_amt = calculate_gst(data["CGST"],amt_before)
      sgst_amt = calculate_gst(data["SGST"],amt_before)
      total_amount_sale_line_item = amt_before + cgst_amt + sgst_amt
      total_amount_after_tax += total_amount_sale_line_item
      total_amount_before_tax += amt_before
      total_cgst_amount += cgst_amt
      total_sgst_amount += sgst_amt
      total_tax_amount += cgst_amt + sgst_amt
      updated_json = data
      currency_code = request_data["currency_code"]
      # format the amount with currency symbol before rendering template
      formatted_total_before_tax = currency.pretty(amt_before,currency_code,trim=True).replace((currency.symbol(currency_code)),(currency.symbol(currency_code)) + " ")
      formatted_cgst_amount = currency.pretty(cgst_amt,currency_code,trim=True).replace((currency.symbol(currency_code)),(currency.symbol(currency_code)) + " ")
      formatted_sgst_amount = currency.pretty(sgst_amt,currency_code,trim=True).replace((currency.symbol(currency_code)),(currency.symbol(currency_code)) + " ")
      formatted_total_amount_sale_line_item = currency.pretty(total_amount_sale_line_item,currency_code,trim=True).replace((currency.symbol(currency_code)),(currency.symbol(currency_code)) + " ")
      updated_json.update({"cgst_amt":formatted_cgst_amount,"sgst_amt":formatted_sgst_amount,"formatted_total_before_tax":formatted_total_before_tax,"total_amount_sale_line_item":formatted_total_amount_sale_line_item})
      server_invoice.append(updated_json)
  total_amount_in_words = num2words(total_amount_after_tax)
  formatted_total_amount_before_tax = currency.pretty(total_amount_before_tax,currency_code,trim=True).replace((currency.symbol(currency_code)),(currency.symbol(currency_code)) + " ")
  formatted_total_cgst_amount = currency.pretty(total_cgst_amount,currency_code,trim=True).replace((currency.symbol(currency_code)),(currency.symbol(currency_code)) + " ")
  formatted_total_sgst_amount = currency.pretty(total_sgst_amount,currency_code,trim=True).replace((currency.symbol(currency_code)),(currency.symbol(currency_code)) + " ")
  formatted_total_tax_amount = currency.pretty(total_tax_amount,currency_code,trim=True).replace((currency.symbol(currency_code)),(currency.symbol(currency_code)) + " ")
  formatted_total_amount_after_tax = currency.pretty(total_amount_after_tax,currency_code,trim=True).replace((currency.symbol(currency_code)),(currency.symbol(currency_code)) + " ")
  formatted_meta_invoice_data = {
    "total_amount_in_words":total_amount_in_words,
    "formatted_total_amount_before_tax":formatted_total_amount_before_tax,
    "formatted_total_cgst_amount":formatted_total_cgst_amount,
    "formatted_total_sgst_amount":formatted_total_sgst_amount,
    "formatted_total_tax_amount":formatted_total_tax_amount,
    "formatted_total_amount_after_tax":formatted_total_amount_after_tax
  }
  user_json = dumps(request_data)
  invoice_meta_data = json.loads(user_json)
  # try server_invoice is array of json so iterate it through for loop
  invoice_url = generateRandomUrl(request_data["company_name"])
  t_data = request_data
  t_data.update({"invoice_url":invoice_url})
  db.history.insert(t_data)
  htmlpage = render_template('index.html',uf_meta=invoice_meta_data,f_meta=formatted_meta_invoice_data,si=server_invoice)
  html_file = open("static/pdf_stored/"+invoice_url+".html","w")
  html_file.write(htmlpage)
  html_file.close()
  invoice_name =invoice_url.replace("%20"," ").replace("%2D","-")
  pdfkit.from_file("static/pdf_stored/"+invoice_url+".html","static/pdf_stored/"+invoice_name+".pdf")
  remove("static/pdf_stored/"+invoice_url+".html")
  external_ip = urllib.request.urlopen('https://ident.me').read().decode('utf8')
  return "https://" + str(external_ip) + ":4004" + "/static/pdf_stored/"+invoice_name+".pdf"

  
@app.route('/invoice/<invoicename>', methods=['GET', 'POST'])
def invoice_history(invoicename):
  # TODO Fetches the files from db and shows option to download
  # TODO Search for saved files, if not found then search in db and generate
  pass

def generateRandomUrl(org_name):
  currentdatestamp = datetime.datetime.now().replace(microsecond=0)
  baseurl = "invoice_" + str(org_name) + "_" + str(currentdatestamp).replace(" ","%20").replace("-","%2D")
  return baseurl


def calculate_gst(percentage,amount_before_tax):
  t_percentage=float(percentage)
  t_amount=float(amount_before_tax)
  t_tax_amount=t_amount*(t_percentage/100)
  return t_amount


if __name__ == '__main__':
  app.run(host='0.0.0.0', port=4004, debug=True)
 