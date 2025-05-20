import quopri

with open("raw_email.txt", "rb") as f:
    raw = f.read()

decoded = quopri.decodestring(raw).decode("utf-8")

with open("decoded_email.html", "w", encoding="utf-8") as f:
    f.write(decoded)