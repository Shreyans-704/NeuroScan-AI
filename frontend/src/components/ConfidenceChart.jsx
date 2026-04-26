import React from 'react';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
} from 'chart.js';
import { Bar } from 'react-chartjs-2';

ChartJS.register(CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend);

const STAGE_COLOURS = {
  'Non-Demented':       { bg: 'rgba(34,197,94,0.75)',  border: 'rgba(34,197,94,1)' },
  'Very Mild Demented': { bg: 'rgba(234,179,8,0.75)',  border: 'rgba(234,179,8,1)' },
  'Mild Demented':      { bg: 'rgba(249,115,22,0.75)', border: 'rgba(249,115,22,1)' },
  'Moderate Demented':  { bg: 'rgba(239,68,68,0.75)',  border: 'rgba(239,68,68,1)' },
};

export default function ConfidenceChart({ confidence, prediction }) {
  // Defensive check
  const safeConfidence = (confidence && typeof confidence === 'object') ? confidence : {};
  
  const labels  = Object.keys(safeConfidence);
  const values  = Object.values(safeConfidence).map((v) => (parseFloat(v) || 0).toFixed(2));
  const bgColours     = labels.map((l) => STAGE_COLOURS[l]?.bg     || 'rgba(37,99,235,0.75)');
  const borderColours = labels.map((l) => STAGE_COLOURS[l]?.border || 'rgba(37,99,235,1)');

  const data = {
    labels,
    datasets: [
      {
        label: 'Confidence (%)',
        data: values,
        backgroundColor: bgColours,
        borderColor: borderColours,
        borderWidth: 2,
        borderRadius: 8,
        borderSkipped: false,
      },
    ],
  };

  const options = {
    responsive: true,
    maintainAspectRatio: true,
    animation: {
      duration: 1000,
      easing: 'easeOutQuart',
    },
    plugins: {
      legend: { display: false },
      tooltip: {
        backgroundColor: '#0F1E35',
        borderColor: '#1E3A5F',
        borderWidth: 1,
        titleColor: '#F1F5F9',
        bodyColor: '#94A3B8',
        padding: 12,
        callbacks: {
          label: (ctx) => ` ${ctx.parsed.y}%`,
        },
      },
    },
    scales: {
      x: {
        grid: { display: false },
        ticks: {
          color: '#94A3B8',
          font: { family: 'Inter', size: 11 },
          maxRotation: 15,
          callback: function(val, i) {
            const lbl = this.getLabelForValue(i) || '';
            return lbl.length > 16 ? lbl.match(/.{1,14}/g) : lbl;
          },
        },
        border: { color: '#1E3A5F' },
      },
      y: {
        min: 0,
        max: 100,
        grid: {
          color: 'rgba(30,58,95,0.4)',
          drawBorder: false,
        },
        ticks: {
          color: '#94A3B8',
          font: { family: 'Inter', size: 11 },
          callback: (val) => `${val}%`,
        },
        border: { color: '#1E3A5F' },
      },
    },
  };

  return (
    <div className="chart-wrapper">
      <Bar data={data} options={options} />
    </div>
  );
}
