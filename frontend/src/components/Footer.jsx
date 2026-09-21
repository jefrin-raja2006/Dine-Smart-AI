export default function Footer() {
  return (
    <footer className="footer">
      <div className="footer-brand">
        <span className="brand-mark">D</span>
        <div>
          <strong>DineSmart AI</strong>
          <span>Find food that fits you.</span>
        </div>
      </div>

      <span>© {new Date().getFullYear()} DineSmart AI</span>
    </footer>
  );
}
