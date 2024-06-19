#include <iostream>

/* run this program using the console pauser or add your own getch, system("pause") or input loop */

int main(int argc, char** argv) {
	int a,b,c,d;
	std::cout<<("enter the numbers:");
	std::cin>>a>>b;
	c = a/b;
	d = a%b;
	std::cout << "The quotient is " << c <<std::endl;
	std::cout << "The remainder is " << d;
	return 0;
}
