# https://www.youtube.com/watch?v=nNQSfRwT0Do

# bank to bank communication

# lendMoney
# transferMoney

struct Transaction {
    1: required Bank fromBank;
    2: required Bank toBank;
    3: required int amount;
}

service BankService {
  bool lendMoney(1: Bank fromBank, 2: Bank toBank, 3: double amount) throws (1: string errorMsg)
  bool transferMoney(1: Transaction transaction) throws (1: string errorMsg)
}
