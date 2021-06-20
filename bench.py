import requests


def extract(crude, text, init, start, end):
	pos = crude.find(text,init)
	if pos == -1:
		return ""
	else:
		phrase = crude[pos+start:pos+end]
		if phrase[0] == "/":
			phrase = phrase[1:]
		name = ""
		for p in phrase:
			if p in "/? ":
				break
			else:
				name += p
	return name


def clean(text):
	r = ''
	for digit in text.strip():
		if digit.isdigit() or digit == ".":
			r += digit
		else:
			break
	return r

def main(url):
	crude = requests.get(url).text
	names, init = [], 0
	while True:
		name = extract(crude, 'href="http', init, 13, 50)
		if not name:
			break
		if not [i for i in ("facebook","instagram","twitter","youtube","linkedin","cuantoestaeldolar","google") if i in name]:
			name = name.replace('www.','')
			name = name[:name.find('.')]
			names.append(name)
		init += 20
	names = set(names)

	d = {}
	for n in names:
		init = crude.find(n)
		compra = clean(extract(crude, 'compra', init, 9, 14).strip())
		if not compra:
			compra = clean(extract(crude, '_compra', init, 30, 36).strip())
		venta = clean(extract(crude, '_venta', init, 8, 14).strip())
		if not venta:
			venta = clean(extract(crude, 'venta', init, 27, 36).strip())
		d.update({n+'_compra': compra, n+'_venta': venta})

	return d


if __name__ == '__main__':
	url = 'https://cuantoestaeldolar.pe'
	print(main(url))