// main.js
import './style.css';
import { Chart } from 'chart.js/auto';

document.addEventListener("DOMContentLoaded", () => {
    // --- Reusable Chart Creation Functions ---

    /**
     * Creates a configured Pie chart.
     * @param {CanvasRenderingContext2D} ctx - The canvas context.
     * @param {string} title - The title of the chart.
     * @returns {Chart} A new Chart.js instance.
     */
    function createPieChart(ctx, title) {
        return new Chart(ctx, {
            type: 'pie',
            data: {
                labels: [],
                datasets: [{
                    label: 'Transaction Count',
                    data: [],
                    backgroundColor: ['rgba(75, 192, 192, 0.8)', 'rgba(54, 162, 235, 0.8)', 'rgba(255, 99, 132, 0.8)', 'rgba(255, 206, 86, 0.8)'],
                    borderColor: '#fff',
                    borderWidth: 2
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { title: { display: true, text: title } }
            }
        });
    }

    /**
     * Creates a configured Bar chart.
     * @param {CanvasRenderingContext2D} ctx - The canvas context.
     * @param {string} title - The title of the chart.
     * @returns {Chart} A new Chart.js instance.
     */
    function createBarChart(ctx, title) {
        return new Chart(ctx, {
            type: 'bar',
            data: {
                labels: [],
                datasets: [{
                    label: 'Usage by Payment Method',
                    data: [],
                    backgroundColor: 'rgba(54, 162, 235, 0.7)',
                    borderColor: 'rgba(54, 162, 235, 1)',
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { title: { display: true, text: title } },
                scales: { y: { beginAtZero: true, ticks: { stepSize: 1 } } }
            }
        });
    }

    /**
     * Creates a configured Line chart for transaction volume.
     * @param {CanvasRenderingContext2D} ctx - The canvas context.
     * @param {string} title - The title of the chart.
     * @returns {Chart} A new Chart.js instance.
     */
    function createLineChart(ctx, title) {
        return new Chart(ctx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [{
                    label: 'Transactions per Interval',
                    data: [],
                    fill: true,
                    backgroundColor: 'rgba(75, 192, 192,0.3)',
                    borderColor: 'rgb(75, 192, 192,0.9)',
                    tension: 0.1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { title: { display: true, text: title } },
                scales: { y: { beginAtZero: true } }
            }
        });
    }

    // --- 1. GET ALL CANVAS CONTEXTS ---
    const charts = {
        source1: {
            status: createPieChart(document.getElementById('myChart1').getContext('2d'), 'Source 1: Transaction Status'),
            payment: createBarChart(document.getElementById('myChart2').getContext('2d'), 'Source 1: Payment Methods'),
            volume: createLineChart(document.getElementById('myChart3').getContext('2d'), 'Source 1: Live Volume'),
            counter: 0
        },
        source2: {
            status: createPieChart(document.getElementById('myChart4').getContext('2d'), 'Source 2: Transaction Status'),
            payment: createBarChart(document.getElementById('myChart5').getContext('2d'), 'Source 2: Payment Methods'),
            volume: createLineChart(document.getElementById('myChart6').getContext('2d'), 'Source 2: Live Volume'),
            counter: 0
        }
    };
    
    const allCharts = [
        charts.source1.status, charts.source1.payment, charts.source1.volume,
        charts.source2.status, charts.source2.payment, charts.source2.volume
    ];

    // --- 2. SETUP EVENT HANDLERS ---
    const button = document.getElementById("resetchartdata");

    function resetAllCharts() {
        console.warn("Resetting all charts!");
        allCharts.forEach(chart => {
            chart.data.labels = [];
            chart.data.datasets[0].data = [];
            chart.update();
        });
        charts.source1.counter = 0;
        charts.source2.counter = 0;
    }
    button.addEventListener("click", resetAllCharts);

    // --- 3. REUSABLE SSE CONNECTION AND UPDATE LOGIC ---


function setupSseConnection(url, targetCharts) {
    const eventSource = new EventSource(url);

    eventSource.onmessage = function (event) {

        // --- 2. SAFELY PARSE THE EXTRACTED STRING ---
        try {
            const transaction = JSON.parse(event.data);

            
            // Add a final safety check in case the 'data' property is missing.
            if (!transaction) {
                console.warn(`Parsed SSE object from ${url} is missing the 'data' property:`, receivedObject);
                return; // Exit early
            }

            console.log(`Successfully processed transaction from ${url}:`, transaction);

            // --- 4. UPDATE CHARTS (This logic can now run without errors) ---
            
            // Update Status Chart (Pie)
            const statusLabel = transaction.status;
            const statusIndex = targetCharts.status.data.labels.indexOf(statusLabel);
            if (statusIndex === -1) {
                targetCharts.status.data.labels.push(statusLabel);
                targetCharts.status.data.datasets[0].data.push(1);
            } else {
                targetCharts.status.data.datasets[0].data[statusIndex]++;
            }

            // Update Payment Chart (Bar)
            const paymentLabel = transaction.payment_method;
            const paymentIndex = targetCharts.payment.data.labels.indexOf(paymentLabel);
            if (paymentIndex === -1) {
                targetCharts.payment.data.labels.push(paymentLabel);
                targetCharts.payment.data.datasets[0].data.push(1);
            } else {
                targetCharts.payment.data.datasets[0].data[paymentIndex]++;
            }

            targetCharts.status.update();
            targetCharts.payment.update();
            targetCharts.counter++;

        } catch (error) {
            // This will catch any final JSON.parse errors if the string is truly malformed.
            console.error(`CRITICAL ERROR processing data from ${url}:`, error);
            console.error("The raw string that caused the parse failure was:", jsonString);
        }
    };

    eventSource.onerror = (error) => console.error(`SSE Connection Error on ${url}:`, error);
}

    // --- 4. SETUP VOLUME CHART UPDATES ---
    const updateInterval = 2000;
    const maxDataPoints = 15;

    setInterval(() => {
        const timeLabel = new Date().toLocaleTimeString();

        // Update both volume charts
        for (const source of Object.values(charts)) {
            source.volume.data.labels.push(timeLabel);
            source.volume.data.datasets[0].data.push(source.counter);
            source.counter = 0; // Reset the counter for the next interval

            if (source.volume.data.labels.length > maxDataPoints) {
                source.volume.data.labels.shift();
                source.volume.data.datasets[0].data.shift();
            }
            source.volume.update();
        }
    }, updateInterval);

    // --- 5. START THE CONNECTIONS ---
    setupSseConnection("http://localhost:8000/real_time_response", charts.source1);
    setupSseConnection("http://localhost:8001/transactions", charts.source2);
});