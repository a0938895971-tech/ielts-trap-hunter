// This interactive website uses an authored, fixed-answer demo only.
// Ollama runs in main.py on the user's own computer, not in GitHub Pages.
const passage = 'The Riverside Science Museum opened in 1998. In 2016 it extended its Friday opening hours by two hours. Its east wing renovation was finished in 2020. Visitors can enter permanent exhibitions without paying, but special exhibitions require a ticket.';
const questions = [
  {statement:'The museum first opened before the year 2000.', answer:'TRUE', evidence:'opened in 1998', explanation:'1998 年早於 2000 年；before the year 2000 是 opened in 1998 的同義改寫。', trap:'同義改寫 / Paraphrase'},
  {statement:'The museum shortened its opening hours on Fridays in 2016.', answer:'FALSE', evidence:'extended its Friday opening hours by two hours', explanation:'文章說的是 extended（延長），題目說 shortened（縮短），兩者明確矛盾。', trap:'反向敘述 / Opposite meaning'},
  {statement:'The museum closed its east wing to the public while it was renovated.', answer:'NOT GIVEN', evidence:'Its east wing renovation was finished in 2020.', explanation:'文章只有提到整修完成的時間，沒有說是否對外關閉；不能使用常識補充資訊。', trap:'缺少資訊 / Missing information'},
];
let current = 0;
let score = 0;
let answered = 0;
const $ = id => document.getElementById(id);
const buttons = Array.from(document.querySelectorAll('[data-answer]'));
function render(){
  const q=questions[current];
  $('progress').textContent=`QUESTION ${String(current+1).padStart(2,'0')} / ${String(questions.length).padStart(2,'0')}`;
  $('passage').textContent=passage;
  $('statement').textContent=q.statement;
  $('feedback').hidden=true;
  $('feedback').replaceChildren();
  $('next').hidden=true;
  buttons.forEach(b=>{b.disabled=false;b.setAttribute('aria-pressed','false')});
  $('score').textContent=`${score} / ${answered} CORRECT`;
}
function answer(chosen){
  if(buttons.some(b=>b.disabled))return;
  const q=questions[current];
  const good=chosen===q.answer;
  if(good)score++;
  answered++;
  buttons.forEach(b=>{b.disabled=true;b.setAttribute('aria-pressed',String(b.dataset.answer===chosen))});
  const feedback=$('feedback');
  const heading=document.createElement('strong');
  heading.textContent=(good?'✓ 你找對證據了！':'✕ 這題藏了陷阱')+`　標準答案：${q.answer}`;
  const evidence=document.createElement('p');
  evidence.textContent=`原文線索：${q.evidence}`;
  const explanation=document.createElement('p');
  explanation.textContent=q.explanation;
  const trap=document.createElement('small');
  trap.textContent=`陷阱類型：${q.trap}`;
  feedback.replaceChildren(heading,evidence,explanation,trap);
  feedback.hidden=false;
  $('score').textContent=`${score} / ${answered} CORRECT`;
  $('next').textContent=current===questions.length-1?'重新練習 ↺':'下一題 →';
  $('next').hidden=false;
}
buttons.forEach(button=>button.addEventListener('click',()=>answer(button.dataset.answer)));
$('next').addEventListener('click',()=>{
  if(current===questions.length-1){current=0;score=0;answered=0}else{current++}
  render();
});
render();
