#include "Subject.h"

Subject::Subject()= default;

Subject::~Subject()= default;

void Subject::attach(shared_ptr<Observer> pObserver){
    m_vtObj.push_back(pObserver);
}

void Subject::detach(shared_ptr<Observer> pObserver){
    auto iter = std::find(m_vtObj.begin(), m_vtObj.end(), pObserver);
    if (iter != m_vtObj.end()){
        m_vtObj.erase(iter);
    }
}

void Subject::notify(){
    for (auto itr: m_vtObj){
        itr->update(shared_from_this()); 
    }
}