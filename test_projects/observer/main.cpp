#include <iostream>
#include "Subject.h"
#include "Observer.h"
#include "ConcreteObserver.h"
#include "ConcreteSubject.h"

using namespace std;

int main(int argc, char *argv[])
{
    auto subject = make_shared<ConcreteSubject>();
    auto objA = make_shared<ConcreteObserver>("A");
    auto objB = make_shared<ConcreteObserver>("B");
    subject->attach(objA);
    subject->attach(objB);
    
    subject->setState(1);
    subject->notify();
    
    cout << "--------------------" << endl;
    subject->detach(objB);
    subject->setState(2);
    subject->notify();

    getchar();
    return 0;
}
