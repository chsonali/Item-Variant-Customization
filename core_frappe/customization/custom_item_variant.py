import frappe
import copy
import json
from frappe import _
from frappe.utils import cstr, flt
from six import string_types

@frappe.whitelist()
def custom_create_variant(item, args):
        if isinstance(args, string_types):
                args = json.loads(args)

        template = frappe.get_doc("Item", item)
        variant = frappe.new_doc("Item")
        variant.variant_based_on = 'Item Attribute'
        variant_attributes = []
        variant_uoms = []
        width =  0
        height = 0
        for d in template.attributes:
                variant_attributes.append({
                        "attribute": d.attribute,
                        "attribute_value": args.get(d.attribute)
                })

                if d.attribute == "Width":
                        frappe.log_error(d.attribute)
                        width = args.get(d.attribute)
                        variant.set("width" ,args.get(d.attribute))
                if d.attribute == "Height":
                        height = args.get(d.attribute)
                        variant.set("height" ,args.get(d.attribute))
                if d.attribute ==  "Yield":
                        variant.set("yield" ,args.get(d.attribute))
        variant.set("attributes", variant_attributes)
        for row in template.uoms:
                if row.uom == "Kg":
                        variant_uoms.append({
                                "uom":row.uom,
                                "formula":template.length*flt(width)*1.441
                        })
                if row.uom == "Cubic Meter":
                        variant_uoms.append({
                                "uom":row.uom,
                                "formula":template.length*flt(width)*flt(height)
                        })
                if row.uom != "Cubic Meter" and row.uom != "Kg":
                        variant_uoms.append({
                                "uom":row.uom,
                                "conversion_factor":row.conversion_factor
                        })
        variant.set("uoms", variant_uoms)
              
        copy_attributes_to_variant(template, variant)
        make_variant_item_code(template.item_code, template.item_name, variant)

        return variant

def copy_attributes_to_variant(item, variant):
	# copy non no-copy fields

	exclude_fields = [
		"naming_series",
		"item_code",
		"item_name",
		"published_in_website",
		"opening_stock",
		"variant_of",
		"valuation_rate",
		"has_variants",
		"attributes",
	]

	if item.variant_based_on == "Manufacturer":
		# don't copy manufacturer values if based on part no
		exclude_fields += ["manufacturer", "manufacturer_part_no"]

	allow_fields = [d.field_name for d in frappe.get_all("Variant Field", fields=["field_name"])]
	if "variant_based_on" not in allow_fields:
		allow_fields.append("variant_based_on")
	for field in item.meta.fields:
		# "Table" is part of `no_value_field` but we shouldn't ignore tables
		if (field.reqd or field.fieldname in allow_fields) and field.fieldname not in exclude_fields:
			if variant.get(field.fieldname) != item.get(field.fieldname):
				if field.fieldtype == "Table":
					variant.set(field.fieldname, [])
					for d in item.get(field.fieldname):
						row = copy.deepcopy(d)
						if row.get("name"):
							row.name = None
						variant.append(field.fieldname, row)
				else:
					variant.set(field.fieldname, item.get(field.fieldname))

	variant.variant_of = item.name

	if "description" not in allow_fields:
		if not variant.description:
			variant.description = ""
	else:
		if item.variant_based_on == "Item Attribute":
			if variant.attributes:
				attributes_description = item.description + " "
				for d in variant.attributes:
					attributes_description += "<div>" + d.attribute + ": " + cstr(d.attribute_value) + "</div>"

				if attributes_description not in variant.description:
					variant.description = attributes_description


def make_variant_item_code(template_item_code, template_item_name, variant):
	"""Uses template's item code and abbreviations to make variant's item code"""
	if variant.item_code:
		return

	abbreviations = []
	for attr in variant.attributes:
		item_attribute = frappe.db.sql(
			"""select i.numeric_values, v.abbr
			from `tabItem Attribute` i left join `tabItem Attribute Value` v
				on (i.name=v.parent)
			where i.name=%(attribute)s and (v.attribute_value=%(attribute_value)s or i.numeric_values = 1)""",
			{"attribute": attr.attribute, "attribute_value": attr.attribute_value},
			as_dict=True,
		)

		if not item_attribute:
			continue
			# frappe.throw(_('Invalid attribute {0} {1}').format(frappe.bold(attr.attribute),
			# 	frappe.bold(attr.attribute_value)), title=_('Invalid Attribute'),
			# 	exc=InvalidItemAttributeValueError)

		abbr_or_value = (
			cstr(attr.attribute_value) if item_attribute[0].numeric_values else item_attribute[0].abbr
		)
		abbreviations.append(abbr_or_value)

	if abbreviations:
		variant.item_code = "{0}-{1}".format(template_item_code, "-".join(abbreviations))
		variant.item_name = "{0}-{1}".format(template_item_name, "-".join(abbreviations))


