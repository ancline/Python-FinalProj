// Function to handle successful QR scan
function onScanSuccess(decodedText, decodedResult) {
  const resultDiv = document.getElementById("result");
  resultDiv.innerText = `Decoded QR Code: ${decodedText}`;
  resultDiv.classList.add("show");

  // Optional: Stop scanning after successful scan
  // qrCodeScanner.clear();
}

// Function to handle any scanning errors
function onScanError(errorMessage) {
  // Silently handle errors (camera permission, no QR code detected, etc.)
  // console.warn(`QR Scan error: ${errorMessage}`);
}

// Initialize the QR code scanner
const qrCodeScanner = new Html5QrcodeScanner(
  "qr-reader",
  {
    fps: 10,
    qrbox: { width: 250, height: 250 },
  },
  false
);

// Start the scanner
qrCodeScanner.render(onScanSuccess, onScanError);
