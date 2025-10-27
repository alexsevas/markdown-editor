# Расширенный тест LaTeX формул

## 1. Inline формулы (стандартные)

Формула Эйнштейна: $E = mc^2$

Квадратное уравнение: $x = \frac{-b \pm \sqrt{b^2 - 4ac}}{2a}$

## 2. Display формулы с $$...$$

$$\int_{-\infty}^{\infty} e^{-x^2} dx = \sqrt{\pi}$$

$$P(A|B) = \frac{P(B|A) \cdot P(A)}{P(B)}$$

## 3. Display формулы с \[ ... \]

\[
\sum_{i=1}^{n} i = \frac{n(n+1)}{2}
\]

\[
\nabla \times \vec{E} = -\frac{\partial \vec{B}}{\partial t}
\]

## 4. Inline формулы с \( ... \)

Скорость света \( c = 3 \times 10^8 \) м/с

Ускорение \( a = \frac{dv}{dt} \)

## 5. Одиночные LaTeX команды (без обрамления)

Единицы измерения: 10 \text{см}, 5 \text{кг}, 20 \text{м/с}

Дроби: \frac{1}{2}, \frac{3}{4}, \frac{20}{100}

Векторы: \vec{a}, \vec{b}, \vec{F}, \overrightarrow{AB}, \overrightarrow{CD}

Стрелки: \uparrow, \downarrow, \leftarrow, \rightarrow, \implies, \iff

Операторы: \cdot, \times, \div, \pm, \mp

Корни: \sqrt{2}, \sqrt{3}, $\sqrt[3]{8}$

Надчеркивание: \overline{AB}, \underline{text}

Шляпки: \hat{x}, \bar{y}, \tilde{z}

Рамки: \boxed{x = 5}, \boxed{E = mc^2}

## 6. Смешанный текст с формулами

Рассмотрим вектор \vec{a} с модулем |\vec{a}| = 10 \text{м/с}. 

Тогда его проекция на ось X равна a_x = |\vec{a}| \cdot \cos\alpha.

Из этого следует \implies что a_x \leq |\vec{a}|.

## 7. Сложные формулы

Уравнение Шрёдингера:

$$i\hbar\frac{\partial}{\partial t}\Psi(\mathbf{r},t) = \hat{H}\Psi(\mathbf{r},t)$$

Преобразование Лоренца:

\[
t' = \gamma \left(t - \frac{vx}{c^2}\right), \quad x' = \gamma(x - vt)
\]

где $\gamma = \frac{1}{\sqrt{1 - \frac{v^2}{c^2}}}$

## 8. Матрицы и системы

Матрица поворота:

$$\begin{pmatrix} \cos\theta & -\sin\theta \\ \sin\theta & \cos\theta \end{pmatrix}$$

Система уравнений:

\[
\begin{cases}
x + y = 5 \\
2x - y = 1
\end{cases}
\]

## 9. Греческие буквы и специальные символы

Греческие: \alpha, \beta, \gamma, \delta, \epsilon, \theta, \lambda, \mu, \pi, \sigma, \omega

Заглавные: \Delta, \Gamma, \Lambda, \Omega, \Sigma, \Phi, \Psi

Специальные: \infty, \partial, \nabla, \hbar, \ell, \Re, \Im

## 10. Физические формулы

Второй закон Ньютона: \vec{F} = m\vec{a}

Закон всемирного тяготения: F = G\frac{m_1 m_2}{r^2}

Кинетическая энергия: E_k = \frac{mv^2}{2}

Импульс: \vec{p} = m\vec{v}

Работа: A = \vec{F} \cdot \vec{s} = Fs\cos\alpha

Мощность: P = \frac{A}{t} = Fv

## 11. Результаты в рамках

Ответ: \boxed{x = 42}

Решение: $\boxed{v = \sqrt{\frac{2E}{m}}}$

Итого: $\boxed{\text{Скорость } = 100 \text{ м/с}}$
