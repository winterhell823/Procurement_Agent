export default function Button({ children, variant = "primary", onClick }) {
  const base = "px-6 py-3 rounded-lg transition";

  const styles = {
    primary:
      "bg-gradient-to-r from-blue-500 to-purple-500 hover:scale-105",
    secondary:
      "border border-gray-600 hover:bg-white/10",
  };

  return (
    <button onClick={onClick} className={`${base} ${styles[variant]}`}>
      {children}
    </button>
  );
}