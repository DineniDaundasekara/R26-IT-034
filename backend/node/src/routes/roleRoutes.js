const express = require('express');
const router = express.Router();
const JobRole = require('../models/JobRole');
const AIServiceClient = require('../services/aiServiceClient');

// Get all roles (standard + custom)
router.get('/', async (req, res) => {
  try {
    const aiRoles = await AIServiceClient.getStandardRoles();
    let customRoles = [];
    if (require('mongoose').connection.readyState === 1) {
      try {
        customRoles = await JobRole.find({ isCustom: true });
      } catch (dbErr) {
        console.warn('[MongoDB] Custom roles query failed, returning standard roles.');
      }
    }


    return res.status(200).json({
      standardRoles: aiRoles.standardRoles || aiRoles.roles || [],
      customRoles: customRoles
    });
  } catch (err) {
    console.error('Failed to fetch roles:', err.message);
    return res.status(500).json({ error: 'Failed to fetch roles', message: err.message });
  }
});


// Save custom role
router.post('/', async (req, res) => {
  try {
    const { roleId, roleName, category, requiredSkills, preferredSkills } = req.body;
    
    let roleDoc = await JobRole.findOne({ roleId });
    if (roleDoc) {
      roleDoc.roleName = roleName;
      roleDoc.category = category;
      roleDoc.requiredSkills = requiredSkills;
      roleDoc.preferredSkills = preferredSkills;
    } else {
      roleDoc = new JobRole({
        roleId,
        roleName,
        category,
        requiredSkills,
        preferredSkills,
        isCustom: true
      });
    }

    await roleDoc.save();
    return res.status(200).json({ status: 'SUCCESS', role: roleDoc });
  } catch (err) {
    return res.status(500).json({ error: 'Failed to save role', message: err.message });
  }
});

module.exports = router;
