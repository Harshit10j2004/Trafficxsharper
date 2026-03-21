function TimeSelector() {

  return (

    <div style={{
      marginBottom: "20px",
      display: "flex",
      gap: "10px"
    }}>

      <button style={buttonStyle}>Last 5 min</button>
      <button style={buttonStyle}>Last 15 min</button>
      <button style={buttonStyle}>Last 1 hour</button>

    </div>

  );

}

const buttonStyle = {
  background: "#1f2937",
  color: "white",
  border: "1px solid #374151",
  padding: "6px 12px",
  borderRadius: "6px",
  cursor: "pointer"
};

export default TimeSelector;