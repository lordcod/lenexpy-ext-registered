import openpyxl

ws = openpyxl.load_workbook(
    r"C:\Users\2008d\Downloads\Telegram Desktop\Сетевые_соревнования_по_плаванию_среди_детей_членов_клуба_и_учеников.xlsx")
sheet = ws.active

data = {('Не',): '', ('Нет',): '', ('Пепанян', 'Валерия'): 'Пепанян', ('Данилин', 'Даниил'): 'Данилин', ('Сафонов', 'Роман'): 'Сафонов', ('Самостоятельно',): '', ('Занимаюсь', 'сам'): '', ('нет',): '', ('Сафонов', 'Р.Р.'): 'Сафонов', ('Вадим', 'Бурганов'): 'Бурганов', ('-',): '', ('Никишин', 'Андерей'): 'Никишин', ('Никишин', 'Андрей'): 'Никишин', ('Каплин', 'Егор'): 'Каплин', ('Ирина', 'Зуева'): 'Зуева', ('Егор', 'Каплин'): 'Каплин', ('Курмалеев', 'Ринат'): 'Курмалеев', ('Курималеев', 'Ринат'): 'Курималеев'}

for i, row in enumerate(sheet.iter_rows(min_row=443, values_only=True), start=443):
    print(row)
    final = row[8]
    coach = tuple(row[7].split())
    if len(coach) != 3:
        print(coach)
        if coach not in data:
            res = data[coach] = input(f'>')
        else:
            res = data[coach]
        if res:
            final += f' ({res})'
    else:
        final += f' ({coach[0]})'

    sheet[f'J{i}'] = final

print(data)
ws.save('test.xlsx')
