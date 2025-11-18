import yadisk


def main():
    with yadisk.Client("application-id>", "<application-secret>") as client:
        url = client.get_code_url()

        print(f"Go to the following url: {url}")
        code = input("Enter the confirmation code: ")

        try:
            response = client.get_token(code)
        except yadisk.exceptions.BadRequestError:
            print("Bad code")
            return

        client.token = response.access_token

        if client.check_token():
            print("Sucessfully received token!")
        else:
            print("Something went wrong. Not sure how though...")

main()
