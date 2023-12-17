#include <iostream>
#include "Subject.h"
#include "Observer.h"
#include "ConcreteObserver.h"
#include "ConcreteSubject.h"
#include <Windows.h>

int main(int argc, char *argv[])
{
    auto subject = std::make_shared<ConcreteSubject>();
    auto objA = std::make_shared<ConcreteObserver>("A");
    auto objB = std::make_shared<ConcreteObserver>("B");
    subject->attach(objA);
    subject->attach(objB);
    
    subject->setState(1);
    subject->notify();
    
    std::cout << "---- pid = " << GetCurrentProcessId() << " ----" << std::endl;
    subject->detach(objB);
    subject->setState(2);
    subject->notify();

    getchar();
    return 0;
}
