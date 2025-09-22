function drawCateChart(labels, data) {
  const ctx = document.getElementById('cateChart');

  new Chart(ctx, {
    type: 'pie',
    data: {
      labels: labels,
      datasets: [{
        label: 'Số lượng',
        data: data,
        borderWidth: 1
      }]
    },
    options: {
      scales: {
        y: {
          beginAtZero: true
        }
      }
    }
  });
}

function drawRevenueChart(labels, revenues, quantities) {
  const ctx = document.getElementById('cateChart');

  new Chart(ctx, {
    type: 'bar',
    data: {
      labels: labels,
      datasets: [
        {
          type: 'bar',
          label: 'Doanh thu (VNĐ)',
          data: revenues,
          yAxisID: 'y1',
          borderWidth: 1,
          backgroundColor: 'rgba(220, 53, 69, 0.7)'
        },
        {
          type: 'line',
          label: 'Số lượng',
          data: quantities,
          yAxisID: 'y2',
          borderColor: 'rgba(25, 135, 84, 0.9)',
          backgroundColor: 'rgba(25, 135, 84, 0.3)',
          tension: 0.3,
          fill: true
        }
      ]
    },
    options: {
      responsive: true,
      interaction: { mode: 'index', intersect: false },
      stacked: false,
      scales: {
        y1: {
          type: 'linear',
          position: 'left',
          beginAtZero: true,
          ticks: { callback: (v) => v.toLocaleString() }
        },
        y2: {
          type: 'linear',
          position: 'right',
          beginAtZero: true,
          grid: { drawOnChartArea: false }
        }
      }
    }
  });
}