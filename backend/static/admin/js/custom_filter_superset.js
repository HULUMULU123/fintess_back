document.addEventListener("DOMContentLoaded", function () {
  const style = document.createElement("style");
  style.innerHTML = `

  .inline-group tr {
  display: flex;
  justify-content: space-between;
  /* Чтобы ряды были по ширине всей таблицы */
  width: 110%;
}

.inline-group td {
  /* Чтобы ячейки в строке не ломались */
  flex: 1;
  /* Можно добавить отступы для пространства */
  padding: 0 10px;
}
.inline-related table.tabular tr.form-row td,
.inline-related table.tabular tr.form-row th {
    padding: 0.4rem;
    font-size: 0.875rem;
}

td.original{
display:none;}

.inline-related table.tabular tr.form-row td input,
.inline-related table.tabular tr.form-row td select {
    width: 100%;
    box-sizing: border-box;
    padding: 0.375rem 0.75rem;
    font-size: 0.875rem;
    height: auto;
}

/* Для маленьких экранов */
@media (max-width: 768px) {
 .inline-group td input,
  tr {
    flex-direction:column;
    
  }



  th.original {
  display:none;}
    td.original  {
      display: none !important;
    }
  `;
  document.head.appendChild(style);
  const updateExercises = (supersetSelect) => {
    const supersetId = supersetSelect.value;

    // Ищем рядом, но если не найдёт — fallback ко всему документу
    const container = supersetSelect.closest(".inline-group") || document;
    console.log(container);
    container
      .querySelectorAll('select[id$="superset_exercise"]')
      .forEach(function (exerciseSelect) {
        if (!exerciseSelect.dataset.originalOptions) {
          exerciseSelect.dataset.originalOptions = exerciseSelect.innerHTML;
        }

        const parser = new DOMParser();
        const htmlDoc = parser.parseFromString(
          `<select>${exerciseSelect.dataset.originalOptions}</select>`,
          "text/html"
        );
        const allOptions = htmlDoc.querySelector("select").options;

        exerciseSelect.innerHTML = "";
        for (let option of allOptions) {
          if (option.dataset.superset == supersetId || option.value === "") {
            exerciseSelect.appendChild(option.cloneNode(true));
          }
        }
      });
  };

  document
    .querySelectorAll('select[id$="superset"]')
    .forEach(function (supersetSelect) {
      supersetSelect.addEventListener("change", function () {
        updateExercises(this);
      });

      if (supersetSelect.value) {
        updateExercises(supersetSelect);
      }
    });

  console.log("custom_filter_superset.js loaded");
});
