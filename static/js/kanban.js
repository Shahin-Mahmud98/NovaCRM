function initKanban(moveUrlTemplate, csrfToken) {
  const cards = document.querySelectorAll('.kanban-card');
  const columns = document.querySelectorAll('.kanban-cards');

  cards.forEach(card => {
    card.setAttribute('draggable', 'true');
    card.addEventListener('dragstart', () => card.classList.add('dragging'));
    card.addEventListener('dragend', () => card.classList.remove('dragging'));
  });

  columns.forEach(column => {
    column.addEventListener('dragover', e => {
      e.preventDefault();
      column.closest('.kanban-column').classList.add('kanban-column-drop-hint');
      const dragging = document.querySelector('.dragging');
      const after = getDragAfterElement(column, e.clientY);
      if (!dragging) return;
      if (after == null) {
        column.appendChild(dragging);
      } else {
        column.insertBefore(dragging, after);
      }
    });
    column.addEventListener('dragleave', () => {
      column.closest('.kanban-column').classList.remove('kanban-column-drop-hint');
    });
    column.addEventListener('drop', e => {
      e.preventDefault();
      column.closest('.kanban-column').classList.remove('kanban-column-drop-hint');
      const dragging = document.querySelector('.dragging');
      if (!dragging) return;
      const dealId = dragging.dataset.dealId;
      const stageId = column.dataset.stageId;
      fetch(moveUrlTemplate.replace('0', dealId), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrfToken },
        body: JSON.stringify({ stage_id: stageId }),
      }).then(() => window.location.reload());
    });
  });

  function getDragAfterElement(container, y) {
    const els = [...container.querySelectorAll('.kanban-card:not(.dragging)')];
    return els.reduce((closest, child) => {
      const box = child.getBoundingClientRect();
      const offset = y - box.top - box.height / 2;
      if (offset < 0 && offset > closest.offset) {
        return { offset, element: child };
      }
      return closest;
    }, { offset: Number.NEGATIVE_INFINITY }).element;
  }
}
