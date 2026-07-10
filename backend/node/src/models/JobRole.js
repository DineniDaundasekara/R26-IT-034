const mongoose = require('mongoose');

const JobRoleSchema = new mongoose.Schema({
  roleId: {
    type: String,
    required: true,
    unique: true
  },
  roleName: {
    type: String,
    required: true
  },
  category: {
    type: String,
    default: 'Software Engineering'
  },
  escoReferenceUri: {
    type: String
  },
  requiredSkills: [
    {
      name: { type: String, required: true },
      canonical: { type: String },
      category: { type: String },
      importance: { type: Number, default: 1.0 },
      aliases: [{ type: String }]
    }
  ],
  preferredSkills: [
    {
      name: { type: String, required: true },
      canonical: { type: String },
      category: { type: String },
      importance: { type: Number, default: 0.7 },
      aliases: [{ type: String }]
    }
  ],
  isCustom: {
    type: Boolean,
    default: false
  },
  createdAt: {
    type: Date,
    default: Date.now
  }
});

module.exports = mongoose.model('JobRole', JobRoleSchema);
