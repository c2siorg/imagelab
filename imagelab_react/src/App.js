import './App.css';
import Workspace from './components/Workspace/Workspace';
import Dashboard from './components/Dashboard/Dashboard';
import React from "react";
import {Routes , Route} from 'react-router-dom';
import Profile from './components/Profile/Profile';

function App() {
  return (
    <>
      <Routes>
        <Route path='/' element={<Workspace/>}></Route>
        <Route path='/workspace' element={<Workspace/>}></Route>
        <Route path='/dashboard' element={<Dashboard/>}></Route>
        <Route path='/profile' element={<Profile/>}></Route>
      </Routes>
    </>
  )
}

export default App;