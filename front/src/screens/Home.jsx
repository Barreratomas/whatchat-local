import React from "react";
import "../styles/home.css";
import { Outlet, useLocation } from "react-router-dom";
const Home = () => {
  const location = useLocation(); 


  return (
    <div className="home">
     
      <div className="content">
        <Outlet />
        {location.pathname === "/" && (
          <div className="content-home">
            <h1 className="home-info">WhatChat</h1>
          </div>
        )}
      </div>
    </div>
  );
};

export default Home;
