import smtplib
server = smtplib.SMTP("smtp.gmail.com", 587)
server.starttls()
server.login("akash.maji.technocrat@gmail.com", "txre ueou mtki elnc")
print("Login successful!")
server.quit()
