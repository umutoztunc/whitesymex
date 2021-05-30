#include <stdio.h>
#include <string.h>

int main() {
  char password[32]; 
  fgets(password, sizeof(password), stdin);
  password[strcspn(password, "\r\n")] = '\0';

  if (strcmp(password, "p4ssw0rd") == 0) {
    puts("Correct!");
  } else {
    puts("Nope.");
  }
  return 0;
}
