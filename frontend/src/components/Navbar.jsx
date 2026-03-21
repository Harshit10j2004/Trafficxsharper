function Navbar() {

  return (
    <div style={{
      background:"#0f172a",
      padding:"15px 30px",
      display:"flex",
      justifyContent:"space-between",
      alignItems:"center",
      borderBottom:"1px solid #1f2937"
    }}>

      <h2 style={{margin:0}}>Real Time Metrics Dashboard</h2>

      <div>
        <span style={{marginRight:"20px"}}>Frontend Dashboard</span>
      </div>

    </div>
  );

}

export default Navbar;